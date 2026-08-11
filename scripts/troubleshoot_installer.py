#!/usr/bin/env python3
from scripts.installer_doctor import preflight,print_report
def main():
    r=preflight(repair=True);print_report(r);return 0 if r.get("ready") else 1
if __name__=="__main__":raise SystemExit(main())
