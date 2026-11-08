import json
import pytest
from scripts.dataset_config import check_output_period, period_label


def test_quarter_label_uses_actual_months():
    assert period_label({'year':2025,'months':[7,8,9]}) == '2025-07-01/2025-09-30'
    assert period_label({'year':2025,'months':[1,2,3]}) == '2025-01-01/2025-03-31'


@pytest.mark.parametrize('filename', ['quality_report.json','provenance.json'])
def test_other_quarter_cannot_overwrite_outputs_or_samples(tmp_path, filename):
    path = tmp_path / filename
    path.write_text(json.dumps({'year':2025,'months':[1,2,3]}))
    original = path.read_bytes()
    with pytest.raises(ValueError, match='another period'):
        check_output_period(tmp_path, 2025, [7,8,9], filename)
    assert path.read_bytes() == original
    check_output_period(tmp_path, 2025, [1,2,3], filename)
