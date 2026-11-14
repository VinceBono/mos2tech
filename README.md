# mos2tech

Type in a military occupation code. Get the civilian tech roles closest to it, the skill gaps for each, and the certifications people usually start with. Every result links to its public source.

```
$ mos2tech 2841 --service marines -n 2

2841  Ground Electronics Transmission Systems Maintainer  (Marine Corps, enlisted)

Civilian equivalents (O*NET military crosswalk):
  49-2021.00  Radio, Cellular, and Tower Equipment Installers and Repairers
      https://www.onetonline.org/link/summary/49-2021.00

Closest tech roles (fit = share of the role's important skill and knowledge levels you already meet):

1. Computer Network Support Specialists  (15-1231.00)  fit 88%
     gap: Computers and Electronics: level 4.4 -> 6.58
     gap: Reading Comprehension: level 3.1 -> 3.88
     gap: Critical Thinking: level 3.1 -> 3.75
     gap: Active Listening: level 3.1 -> 3.62
     common certs: CompTIA Network+, Cisco CCNA
     https://www.onetonline.org/link/summary/15-1231.00

2. Information Security Analysts  (15-1212.00)  fit 86%
     ...
```

## Why this exists

People leaving the military are rarely told which tech jobs their occupation is close to, or what they'd be missing. The data to answer that is public. The U.S. Department of Labor rates every civilian occupation on the same skill and knowledge scales, and the Defense Manpower Data Center maps military codes to those occupations. This tool joins the two.

## Install and run

No dependencies, Python 3.10+.

```bash
# run without installing
uvx --from git+https://github.com/VinceBono/mos2tech mos2tech 0631 --service marines

# or install
pip install git+https://github.com/VinceBono/mos2tech
mos2tech 3D0X2 --service "air force"
mos2tech 0631 -s M --json      # machine-readable
```

Services: Army, Navy, Air Force, Marine Corps, Coast Guard, Space Force. If a code exists in only one service you can leave `--service` out.

## How it works

1. **Crosswalk.** Look the code up in the Military Crosswalk and get its civilian O*NET occupations.
2. **Your starting profile.** Take the O*NET *level* ratings (0–7) for those occupations across 67 skill and knowledge areas. If there are several occupations, average them.
3. **Compare to tech roles.** For each of the 27 rated computer occupations, look only at the areas O*NET marks as important for that role (importance 3 or more out of 5). Where the role needs a higher level than your starting profile, that shortfall is a gap.
4. **Fit.** `fit = 1 − (importance-weighted shortfall ÷ importance-weighted requirement)`. 100% means the starting profile meets every important requirement.
5. **Certifications** come from a short hand-written list in [`mos2tech/certs.json`](mos2tech/certs.json). They're common starting points, not O*NET data.

The whole method is about 100 lines in [`mos2tech/core.py`](mos2tech/core.py).

## Limits you should know

- **It rates the occupation, not you.** The levels describe a typical civilian in the equivalent job. Your own experience may be well above or below.
- **Combat arms and some IT codes get no gap analysis.** O*NET doesn't survey military-only occupations (such as Infantry) or "All Other" categories (where the Army's 25B lands). For those codes the tool shows the crosswalk and says so. About three quarters of active codes do have ratings.
- **The crosswalk is coarse.** One code usually maps to one civilian occupation, and it misses much of what the job really involved.
- **Certifications are opinion.** Check job postings in your area before paying for an exam.
- **No language model is used.** Results are a lookup and arithmetic, so they're repeatable and every number can be traced.

## Paying for certifications

- The GI Bill can reimburse licensing and certification test fees: <https://www.va.gov/education/about-gi-bill-benefits/how-to-use-benefits/licensing-and-certification-tests/>
- DoD COOL lists credentials by military occupation while you're still serving: <https://www.cool.osd.mil/>

## Data and licenses

Code is MIT. The files in `mos2tech/onet/` are derived from:

- **O\*NET 31.0 Database** by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), used under the [CC BY 4.0](https://www.onetcenter.org/license_db.html) license. O\*NET® is a trademark of USDOL/ETA. The data has been reduced to occupation titles and level and importance ratings; USDOL/ETA has not approved, endorsed or tested these modifications.
- **Military Crosswalk** (July 2024), source Defense Manpower Data Center, distributed at <https://www.onetcenter.org/crosswalks.html>.

To rebuild them from fresh downloads: `python scripts/build_data.py <crosswalk.csv> <db_text_dir>`.

## Development

```bash
uvx --with-editable . pytest -q tests
uvx ruff check .
python scripts/commitguard.py --all
```
