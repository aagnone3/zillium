# zillium
Real estate visualization with Zillow + Folium

## Prerequisite(s)
- [Docker](https://docs.docker.com/)
- `make build`

## Running
```python
# view options
make help

# run the scripts
make atlanta_heatmap
# or
make price_by_state

# launch a Jupyter notebook
make jup
```

## BYO Data
- Obtain a Zillow Web Services ID (ZSID)
- define this key as `ZILLOW_WSID` in `env`
- set `generate_new = True` in the script/notebook, and customize away
