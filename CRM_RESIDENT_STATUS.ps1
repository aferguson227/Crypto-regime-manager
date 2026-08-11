$ErrorActionPreference='Continue'
Set-Location 'C:\Crypto\Projects'
python -m scripts.crm_resident_control status
python -m scripts.crm_resident_health
exit $LASTEXITCODE
