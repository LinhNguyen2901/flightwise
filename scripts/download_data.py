"""Acquire the two official BTS sources; keep verified existing files immutable."""
import argparse
import hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import zipfile

import requests
try:
    from .dataset_config import active_dataset
except ImportError:
    from dataset_config import active_dataset

ROOT = Path(__file__).resolve().parents[1]
AIRPORT_URL = ('https://transtats.bts.gov/DL_SelectFields.aspx?'
               'QO_fu146_anzr=N8vn6v10+f722146+gnoyr5&gnoyr_VQ=FLL')
FLIGHT_URL = ('https://transtats.bts.gov/PREZIP/'
              'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip')


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
        self.active = False
        self.form_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.form_stack.append(a.get('id') == 'form1')
            self.active = any(self.form_stack)
        if self.active and tag == 'input' and a.get('name'):
            name = a['name']
            if a.get('type') == 'hidden':
                self.fields[name] = a.get('value', '')
            elif a.get('type') == 'checkbox' and name.isupper():
                self.fields[name] = 'on'

    def handle_endtag(self, tag):
        if tag == 'form':
            if self.form_stack:
                self.form_stack.pop()
            self.active = any(self.form_stack)


def acquire(session, path, url, manifest, airport=False):
    key = path.relative_to(ROOT).as_posix()
    if path.exists():
        entry = manifest['files'].get(key)
        if not entry or sha256(path) != entry['sha256']:
            raise ValueError(f'Existing input has no matching provenance/hash: {path}')
        print(f'Verified existing {path.name}', flush=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if airport:
        page = session.get(url, timeout=(20, 120))
        page.raise_for_status()
        form = DownloadForm()
        form.feed(page.text)
        if 'AIRPORT_SEQ_ID' not in form.fields:
            raise ValueError('BTS form changed: missing AIRPORT_SEQ_ID')
        fields = {**form.fields, 'cboGeography': 'All', 'cboYear': 'All',
                  'cboPeriod': 'All', 'btnDownload': 'Download'}
        response = session.post(url, data=fields, timeout=(20, 180), stream=True)
        selected = sorted(k for k in form.fields if not k.startswith('__'))
    else:
        response = session.get(url, timeout=(20, 180), stream=True)
        selected = 'Full monthly pre-zipped export; processing selects documented fields'
    response.raise_for_status()
    temporary = path.with_suffix('.zip.part')
    with open(temporary, 'wb') as target:
        for chunk in response.iter_content(1024 * 1024):
            target.write(chunk)
    if not zipfile.is_zipfile(temporary):
        raise ValueError(f'BTS did not return ZIP; inspect {temporary}')
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupt ZIP')
        members = archive.namelist()
    temporary.rename(path)
    manifest['files'][key] = {
        'source_url': url, 'resolved_url': response.url,
        'retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'bytes': path.stat().st_size, 'sha256': sha256(path),
        'method': 'BTS form POST, all fields' if airport else 'BTS PREZIP GET',
        'selected_fields': selected, 'archive_members': members,
    }
    (ROOT / 'data/manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'Downloaded {path.name}: {path.stat().st_size:,} bytes', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    active = active_dataset()
    parser.add_argument('--year', type=int, default=active['year'])
    parser.add_argument('--months', type=int, nargs='+', default=active['months'])
    args = parser.parse_args()
    if any(m not in range(1, 13) for m in args.months):
        parser.error('months must be 1..12')
    manifest_path = ROOT / 'data/manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'files': {}}
    with requests.Session() as session:
        session.headers['User-Agent'] = 'FlightWise university data visualization project'
        for month in sorted(set(args.months)):
            url = FLIGHT_URL.format(year=args.year, month=month)
            acquire(session, ROOT / 'data/raw' / url.rsplit('/', 1)[1], url, manifest)
        acquire(session, ROOT / 'data/raw/airport_coordinates.zip', AIRPORT_URL, manifest, airport=True)


if __name__ == '__main__':
    main()
