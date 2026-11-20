"""Local, dependency-free SR presentation. Never calls OCI or changes a case."""
import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import quote


def _md(value):
    # Display evidence as text, without activating embedded images or HTML.
    text = escape(str(value), quote=False)
    return re.sub(r'([\\`*_\[\]#|!])', r'\\\1', text)


class _DisplayHTML(HTMLParser):
    """Render a small set of correspondence tags as inert text structure."""
    known = {'p', 'div', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i',
             'span', 'a', 'pre', 'code'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'div', 'pre', 'ul', 'ol'):
            self.parts.append('\n\n')
        elif tag == 'br':
            self.parts.append('\n')
        elif tag == 'li':
            self.parts.append('\n- ')
        elif tag not in self.known:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'pre', 'ul', 'ol'):
            self.parts.append('\n\n')
        elif tag == 'li':
            self.parts.append('\n')
        elif tag not in self.known:
            self.parts.append('</' + tag + '>')

    def handle_data(self, data):
        self.parts.append(data)


def _pretty_json(text):
    """Indent valid object/array JSON without changing tokens or duplicate keys."""
    if not text.lstrip().startswith(('{', '[')):
        return None
    def reject_constant(value):
        raise ValueError(value)
    try:
        json.loads(text, parse_constant=reject_constant)
    except (ValueError, TypeError, RecursionError):
        return None
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[{}\[\],:]|[^\s{}\[\],:]+', text)
    output, depth = [], 0
    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index else None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if token in ('{', '['):
            output.append(token)
            depth += 1
            if following not in ('}', ']'):
                output.append('\n' + '  ' * depth)
        elif token in ('}', ']'):
            depth -= 1
            if previous not in ('{', '['):
                output.append('\n' + '  ' * depth)
            output.append(token)
        elif token == ',':
            output.append(',\n' + '  ' * depth)
        elif token == ':':
            output.append(': ')
        else:
            output.append(token)
    return ''.join(output)


def _body(value):
    text = str(value)
    pretty = _pretty_json(text)
    if pretty is not None:
        # JSON cannot contain literal newlines within strings. Keep the valid
        # formatted JSON and retain its original lexical tokens and precision.
        return '```json\n' + pretty + '\n```'
    if re.search(r'<(?:p|div|br|ul|ol|li|strong|span|a|pre|code)(?:\s|/?>)', text, re.I):
        parser = _DisplayHTML()
        parser.feed(text)
        parser.close()
        text = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', ''.join(parser.parts)).strip()
    # Actual line breaks are displayed. A literal backslash-n stays literal.
    return '\n'.join('> ' + _md(line) if line else '>' for line in text.split('\n'))


def _pick(data, *keys):
    for key in keys:
        if key in data:
            return data[key]
    return None


def render_markdown(report, raw_path=None):
    """Human view of exact field values. The original JSON remains separate."""
    fields = report.get('sr_fields') or {}
    ticket = fields.get('ticket') or {}
    execution = report.get('execution') or {}
    key = fields.get('key') or fields.get('id')
    target = execution.get('target_key')
    source = execution.get('source')
    lines = []
    if key or target:
        identifier = str(key or target)
        label = 'SR' if key else 'Target SR'
        lines.append('**' + label + ':** [' + _md(identifier) + '](https://support.oracle.com/support/?SR=' + quote(identifier, safe='') + ')')
    elif source == 'DRAFT_PAYLOAD':
        lines.append('**SR:** Not created (draft).')
    else:
        lines.append('**SR:** Identifier not returned by this source; verification pending.')
    if source == 'CACHED_RECEIPT':
        lines.append('**Evidence:** Cached receipt; this is not a new write or a fresh retrieval.')
    title = ticket.get('title')
    if title is not None:
        lines.append('**Title:** ' + _md(title))
    problem_type = _pick(fields, 'problemType', 'problem_type', 'problem-type')
    summary = []
    for label, value in (('Type', problem_type), ('Severity', ticket.get('severity'))):
        if value is not None:
            summary.append('**' + label + ':** ' + _md(value))
    if summary:
        lines.append(' | '.join(summary))
    state = _pick(ticket, 'lifecycleState', 'lifecycle_state', 'lifecycle-state')
    details = _pick(ticket, 'lifecycleDetails', 'lifecycle_details', 'lifecycle-details')
    if state is not None or details is not None:
        lines.append('**Status:** ' + ' / '.join(_md(value) for value in (state, details) if value is not None))
    description = ticket.get('description')
    if description is not None:
        lines.extend(['', '**Description**', '', _body(description)])
    else:
        lines.extend(['', 'Description was not returned by this source; no draft text has been substituted.'])
    item = ((ticket.get('resource') or {}).get('item') or {})
    if item.get('comments') is not None:
        lines.extend(['', '**Update / closing note**', '', _body(item['comments'])])
    attachment = report.get('outgoing_attachment')
    if attachment:
        lines.extend(['', '**Attachment**', '', '```json', json.dumps(attachment, ensure_ascii=False, indent=2), '```'])
    classification = report.get('classification_evidence')
    if classification:
        lines.extend(['', '**Classification evidence**', '', '```json', json.dumps(classification, ensure_ascii=False, indent=2), '```'])
    lines.extend(['', '<details>', '<summary>Technical details</summary>', ''])
    for name, value in execution.items():
        if value is not None:
            lines.append('- **' + _md(name) + ':** ' + _md(value))
    lines.extend(['', '</details>'])
    if raw_path is not None:
        # This is complete helper evidence. Only --raw-response identifies a
        # REST JSON read; do not claim SDK model JSON is the raw HTTP body.
        path = Path(raw_path).resolve().as_posix()
        lines.extend(['', '[Raw output (JSON)](<' + path + '>)'])
    return re.sub(r'\n{3,}', '\n\n', '\n\n'.join(lines)).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Existing helper JSON evidence; never re-fetches the SR')
    parser.add_argument('--output', required=True, help='Readable Markdown output')
    args = parser.parse_args()
    from sr import literal_report
    source = Path(args.input).resolve()
    target = Path(args.output).resolve()
    if source == target:
        parser.error('The readable output cannot overwrite its JSON source')
    record = json.loads(source.read_text(encoding='utf-8-sig'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(literal_report(record), source), encoding='utf-8')
    print(json.dumps({'readable_markdown': str(target), 'raw_json': str(source), 'network_operations': 0}))


if __name__ == '__main__':
    main()
