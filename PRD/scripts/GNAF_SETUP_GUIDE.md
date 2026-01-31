# How to Get NSW Suburb-Postcode Data Using GNAF

## Step 1: Download GNAF Data

GNAF (Geocoded National Address File) is the official Australian government address dataset.

### Download Options:

**Option A: data.gov.au (Free)**
1. Visit: https://data.gov.au/
2. Search for "GNAF" or "Geocoded National Address File"
3. Look for the latest release (e.g., "G-NAF" or "Address File")
4. Download the complete dataset (it will be a large zip file, ~2-3 GB)

**Option B: Geoscape (Direct Source)**
1. Visit: https://geoscape.com.au/data/g-naf/
2. Register for free access
3. Download the G-NAF Core dataset

## Step 2: Extract the GNAF Data

After downloading, extract the ZIP file to a folder, for example:
```
C:\Users\kumar\Downloads\GNAF\
```

The extracted folder should contain PSV (pipe-separated values) files, including:
- `LOCALITY.psv` or similar locality table
- Various state-specific address files

## Step 3: Run the Export Script

You already have the script ready! Use it like this:

```powershell
# Run the script with the path to your extracted GNAF folder
python export_nsw_suburbs_postcodes_gnaf.py C:\Users\kumar\Downloads\GNAF

# Or specify a custom output filename:
python export_nsw_suburbs_postcodes_gnaf.py C:\Users\kumar\Downloads\GNAF nsw_postcodes_suburbs.csv
```

## Step 4: Verify the Output

The script will create `nsw_postcodes_suburbs.csv` with all NSW suburbs and their postcodes.

Example output:
```csv
suburb,postcode
Alexandria,2015
Annandale,2038
Ashfield,2131
...
```

## Expected Results

- The GNAF dataset contains the most accurate and complete Australian address data
- You should get thousands of suburb-postcode combinations for NSW
- All official suburbs and localities will be included

## Troubleshooting

If the script can't find the LOCALITY file:
1. Make sure you extracted the full GNAF download
2. Check the folder structure - the script searches recursively
3. Look for files named `LOCALITY.psv`, `LOCALITY.txt`, or `LOCALITY.csv`

## Alternative: Quick Test

If you want to verify before downloading the full GNAF:
1. The GNAF dataset is quite large
2. You might want to check if your institution/organization already has access
3. Or check if data.gov.au has a sample/subset available

---

**Ready to proceed?** 
Once you download and extract GNAF, just run the command above!
