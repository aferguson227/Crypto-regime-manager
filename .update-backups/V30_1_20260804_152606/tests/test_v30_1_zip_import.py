from pathlib import Path
import csv, zipfile
from scripts.core.data_import import csv_sources, import_file

def test_zip_archive_is_discovered_and_imported(tmp_path: Path):
    csv_path=tmp_path/'BTCUSD_240.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        for i in range(6):
            t=1609459200+i*14400
            w.writerow([t,100+i,102+i,99+i,101+i,10+i,20+i])
    archive=tmp_path/'training.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.write(csv_path,arcname='nested/BTCUSD_240.csv')
    found=csv_sources(archive,tmp_path/'expanded')
    assert len(found)==1
    result=import_file(found[0],tmp_path/'normalised')
    assert result.rows_out==6
    assert result.target_timeframe_minutes==240

def test_zip_slip_is_rejected(tmp_path: Path):
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('../escape.csv','1,2,3,4,5,6,7\n')
    try:
        csv_sources(archive,tmp_path/'expanded')
    except ValueError as exc:
        assert 'Unsafe ZIP path' in str(exc)
    else:
        raise AssertionError('unsafe archive was accepted')
