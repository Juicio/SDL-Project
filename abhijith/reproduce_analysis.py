"""Reproduce the Omaha–Council Bluffs transit/employment accessibility outputs.

Run from this folder: python reproduce_analysis.py
Requires pandas, numpy, scipy, matplotlib. Looks for the filtered EPA CSV at
../EPA_SDL_OmahaCouncilBluffs.csv (repository-root layout) or the supplied
uploaded file names. Does not fetch remote sources or modify the source CSV.
"""
from pathlib import Path
import html
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
FIG = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

candidates = [
    ROOT.parent/'EPA_SDL_OmahaCouncilBluffs.csv',
    ROOT/'EPA_SDL_OmahaCouncilBluffs.csv',
    ROOT.parent/'EPA_SDL_OmahaCouncilBluffs(1).csv',
    Path('/mnt/data/EPA_SDL_OmahaCouncilBluffs(1).csv')
]
source = next((p for p in candidates if p.is_file()), None)
if source is None:
    raise FileNotFoundError('Place EPA_SDL_OmahaCouncilBluffs.csv in the project root (one folder above abhijith).')

df = pd.read_csv(source, dtype={'STATEFP':str,'COUNTYFP':str,'TRACTCE':str,'BLKGRPCE':str,
                                 'GEOID10':str, 'GEOID20':str},low_memory=False)
assert df.shape == (727, 117), f'Unexpected source shape: {df.shape}'
for c in ['Pct_AO0','AutoOwn0','HH','D4A','D4C','D4D','D5BR','D5AR']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
    df.loc[df[c] == -99999,c] = np.nan
for c,n in [('STATEFP',2),('COUNTYFP',3),('TRACTCE',6),('BLKGRPCE',1)]:
    df[c]=df[c].str.strip().str.zfill(n)
df['block_group_id_reconstructed'] = df['STATEFP']+df['COUNTYFP']+df['TRACTCE']+df['BLKGRPCE']
assert df['block_group_id_reconstructed'].nunique() == len(df), 'Geographic components are not unique.'
df['county'] = df['STATEFP'].map({'19':'Iowa','31':'Nebraska'}) + ' / ' + df['COUNTYFP'].map({'055':'Douglas','153':'Sarpy','155':'Pottawattamie'})
assert df['county'].notna().all()
df['carfree_pct'] = 100 * df['Pct_AO0']
cut = float(df['Pct_AO0'].quantile(.75))
df['higher_carfree'] = df['Pct_AO0'] >= cut
median_transit_jobs = float(df['D5BR'].median())
df['relative_gap_flag'] = df['higher_carfree'] & df['D5BR'].notna() & (df['D5BR'] < median_transit_jobs)

def nice(v,dec=1):
    return f'{v:,.{dec}f}' if np.isfinite(v) else 'n/a'

# Overview and coverage
counties = [('Douglas', '31','055'),('Sarpy','31','153'),('Pottawattamie','19','155')]
records=[]
for name, state, county in counties:
    x=df[(df.STATEFP==state)&(df.COUNTYFP==county)]
    rec={'county':name,'block_groups':len(x)}
    for col in ['D4A','D4C','D4D','D5BR','D5AR']:
        rec[col+'_valid']=int(x[col].notna().sum())
        rec[col+'_coverage_pct']=100*rec[col+'_valid']/len(x)
    records.append(rec)
coverage=pd.DataFrame(records)
coverage.to_csv(OUT/'coverage_by_county.csv',index=False)

comparisons=[]
for var,label,unit in [('D4A','Walking distance to stop','meters'),('D4C','Peak-period transit service frequency','frequency'),
                       ('D4D','Transit frequency density','per sq. mile'),('D5BR','Transit-accessible jobs (decay-weighted)','weighted jobs'),
                       ('D5AR','Auto-accessible jobs (decay-weighted)','weighted jobs')]:
    x=df[df[var].notna()]
    pair=x[['Pct_AO0',var]].dropna()
    rho, pval=spearmanr(pair['Pct_AO0'],pair[var])
    comparisons.append({'indicator':var,'description':label,'valid_n':len(pair),
                        'spearman_rho':rho,'spearman_p':pval,
                        'higher_carfree_n':int(x.higher_carfree.sum()),
                        'higher_carfree_median':float(x.loc[x.higher_carfree,var].median()),
                        'other_n':int((~x.higher_carfree).sum()),
                        'other_median':float(x.loc[~x.higher_carfree,var].median()),
                        'unit':unit})
comparison=pd.DataFrame(comparisons)
comparison.to_csv(OUT/'indicator_comparisons.csv',index=False)

all_reconstructed=df[['block_group_id_reconstructed','county','HH','AutoOwn0','Pct_AO0','D4A','D4C','D4D','D5BR','D5AR','higher_carfree','relative_gap_flag']].copy()
all_reconstructed.to_csv(OUT/'cleaned_analysis_blockgroups.csv',index=False)
gap=df.loc[df.relative_gap_flag,['block_group_id_reconstructed','county','HH','AutoOwn0','carfree_pct','D4A','D4C','D4D','D5BR','D5AR']].sort_values(['D5BR','carfree_pct'],ascending=[True,False])
gap.to_csv(OUT/'relative_gap_candidates.csv',index=False)

# Graphs: single chart per figure (no subplots)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':14,'axes.labelsize':10,
                     'figure.dpi':160, 'savefig.dpi':170})
fig,ax=plt.subplots(figsize=(8.8,4.5))
y=np.arange(3)
ax.barh(y-.2,coverage.D5BR_coverage_pct,height=.36,label='Job access by transit (D5BR)')
ax.barh(y+.2,coverage.D4C_coverage_pct,height=.36,label='Service frequency (D4C)')
for pos,values in [(-.2,coverage.D5BR_coverage_pct),(+.2,coverage.D4C_coverage_pct)]:
    for yi,v in zip(y,values): ax.text(v+1,yi+pos, f'{v:.1f}%', va='center',fontsize=9)
ax.set(yticks=y,yticklabels=coverage.county,xlim=(0,110),xlabel='Share of block groups with usable indicator (%)',title='Transit-indicator coverage differs sharply by county')
ax.invert_yaxis();ax.legend(loc='lower right',fontsize=9);ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(FIG/'01_coverage_by_county.png',bbox_inches='tight');plt.close(fig)

obs=df[df.D5BR.notna()].copy()
fig,ax=plt.subplots(figsize=(8.8,5.0))
for k,group,alpha,size in [(False,'Other measured block groups',.50,19),(True,'High car-free / below-median jobs',.95,37)]:
    part=obs[obs.relative_gap_flag==k]
    ax.scatter(part.carfree_pct,part.D5BR,alpha=alpha,s=size,label=group)
ax.axvline(cut*100,linewidth=1,linestyle='--',color='gray')
ax.axhline(median_transit_jobs,linewidth=1,linestyle='--',color='gray')
ax.set(yscale='log',xlabel='Households without a car (%)',ylabel='Transit-accessible jobs (decay-weighted; log scale)',
       title='Car-free share and transit-based access to employment')
ax.legend(loc='lower left',fontsize=8);ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(FIG/'02_carfree_vs_transit_jobs.png',bbox_inches='tight');plt.close(fig)

obsstop=df[df.D4A.notna()].copy()
fig,ax=plt.subplots(figsize=(8.8,4.9))
ax.scatter(obsstop.carfree_pct,obsstop.D4A,s=19,alpha=.55)
ax.set(xlabel='Households without a car (%)',ylabel='Walking distance to nearest transit stop (meters)',
       title='Stop proximity among block groups with measured access')
ax.spines[['top','right']].set_visible(False);fig.tight_layout()
fig.savefig(FIG/'03_carfree_vs_stop_distance.png',bbox_inches='tight');plt.close(fig)

measured=df[df.D5BR.notna()]
fig,ax=plt.subplots(figsize=(8.8,4.9))
groups=[measured.loc[~measured.higher_carfree,'D5BR'],measured.loc[measured.higher_carfree,'D5BR']]
ax.boxplot(groups,patch_artist=False,showfliers=False)
ax.set(xticks=[1,2],xticklabels=[f'Other blocks (n={len(groups[0])})',f'Higher car-free (n={len(groups[1])})'],
       ylabel='Transit-accessible jobs (decay-weighted)',title='Employment access varies within both groups')
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'))
ax.spines[['top','right']].set_visible(False);fig.tight_layout()
fig.savefig(FIG/'04_transit_jobs_by_group.png',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(8.8,4.9))
valid=df[['D5AR','D5BR','higher_carfree']].dropna()
for flag,label in [(False,'Other block groups'),(True,'Higher car-free')]:
    p=valid[valid.higher_carfree==flag]
    ax.scatter(p.D5AR,p.D5BR,alpha=.50,s=20,label=label)
ax.set(xlabel='Auto-accessible jobs (weighted)',ylabel='Transit-accessible jobs (weighted)',
       title='Modeled job accessibility by car versus by transit')
ax.legend(loc='upper left');ax.spines[['top','right']].set_visible(False);fig.tight_layout()
fig.savefig(FIG/'05_transit_vs_auto_jobs.png',bbox_inches='tight');plt.close(fig)

# HTML report: explicit Methods/Results separation, planner-focused figure interpretation.
# This is the same statistical analysis as above; report language only is revised.
import base64
N = len(df)
valid_jobs = int(df.D5BR.notna().sum())
n_hi = int(df.higher_carfree.sum())
hi_observed = int((df.higher_carfree & df.D5BR.notna()).sum())
n_flag = len(gap)
weighted = 100 * df.AutoOwn0.sum() / df.HH.sum()
comp = {row.indicator: row for row in comparison.itertuples()}
fmt = lambda x: f'{x:,.0f}'

def td(v):
    return html.escape(str(v))

coverage_rows = ''.join(
    f'<tr><td>{td(r.county)}</td><td>{r.block_groups}</td><td>{r.D4A_valid} ({r.D4A_coverage_pct:.1f}%)</td>'
    f'<td>{r.D4C_valid} ({r.D4C_coverage_pct:.1f}%)</td><td>{r.D5BR_valid} ({r.D5BR_coverage_pct:.1f}%)</td></tr>'
    for r in coverage.itertuples()
)
comparison_rows = ''.join(
    f'<tr><td><strong>{r.indicator}</strong> — {html.escape(r.description)}</td><td>{r.valid_n}</td>'
    f'<td>{r.spearman_rho:+.3f}</td><td>{r.higher_carfree_median:,.1f}</td><td>{r.other_median:,.1f}</td></tr>'
    for r in comparison.itertuples()
)
gap_rows = ''.join(
    f'<tr><td><code>{td(r.block_group_id_reconstructed)}</code></td><td>{td(r.county)}</td>'
    f'<td>{r.carfree_pct:.1f}%</td><td>{r.D5BR:,.0f}</td>'
    f'<td>{r.D4A:,.1f}' + ('</td></tr>' if np.isfinite(r.D4A) else '</td></tr>')
    for r in gap.head(10).itertuples()
)
# Missing distance is displayed as unavailable rather than as the numeric string "nan".
gap_rows = gap_rows.replace('>nan</td>', '>n/a</td>')

def figure(n, title, img, shows, matters, planners, alt):
    return (f'<section class="figure-block"><h3>Figure {n}. {html.escape(title)}</h3>'
            f'<figure><img src="figures/{img}" alt="{html.escape(alt)}">'
            f'<figcaption>Figure {n}. EPA SLD v3 modeled/observed indicators in the available subset.</figcaption></figure>'
            f'<p><b>What it shows.</b> {shows}</p>'
            f'<p><b>Why it matters.</b> {matters}</p>'
            f'<p><b>How a planner could use it.</b> {planners}</p></section>')

css = '''
:root{--ink:#172942;--sub:#52657b;--line:#dbe4ed;--bg:#f5f8fb;--accent:#076b80;--soft:#eef5f8}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{background:var(--bg);color:var(--ink);font-family:Segoe UI,Arial,sans-serif;margin:0;line-height:1.67}
main{background:#fff;max-width:1020px;margin:32px auto;padding:50px 64px;border:1px solid #e0e7ed;border-radius:12px;box-shadow:0 7px 30px #1c37500c}
h1{font-size:32px;line-height:1.24;margin:.22em 0 .3em}h2{font-size:24px;margin:40px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}h3{font-size:19px;margin:26px 0 11px}
p,li{font-size:15px}.kicker{letter-spacing:.11em;text-transform:uppercase;font-size:12px;font-weight:800;color:var(--accent)}.subtitle{color:var(--sub);font-size:17px;margin:0 0 11px}.meta{color:var(--sub);font-size:13px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:26px 0}.stat{background:var(--soft);padding:16px;border-radius:8px}.stat strong{font-size:27px;display:block}.stat span{font-size:12px;color:var(--sub)}
.callout{border-left:4px solid var(--accent);background:var(--soft);padding:16px 19px;border-radius:4px;margin:22px 0}.callout p{margin:0}.caution{border-left:4px solid #a56f25;padding-left:16px;margin:18px 0}
table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 22px}td,th{border-bottom:1px solid var(--line);text-align:left;padding:10px 9px;vertical-align:top}thead{background:#ecf2f7}code{font-size:.91em;background:#edf2f7;border-radius:3px;padding:2px 4px}
figure{margin:18px 0 18px}figure img{width:100%;height:auto;border:1px solid var(--line);border-radius:8px}figcaption{font-size:12px;color:var(--sub);margin-top:5px}.figure-block{border-bottom:1px solid var(--line);padding-bottom:13px;margin-bottom:24px}
a{color:var(--accent)}ul,ol{padding-left:23px}.small{color:var(--sub);font-size:13px}
@media(max-width:720px){main{margin:0;padding:22px 16px;border:0;border-radius:0}.stats{grid-template-columns:1fr}table{display:block;overflow:auto}h1{font-size:26px}}
'''
parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Transit & Employment Accessibility | Omaha–Council Bluffs</title><style>', css, '</style></head><body><main>',
         '<div class="kicker">IDS team project · individual analysis</div>',
         '<h1>Transit &amp; Employment Accessibility</h1>',
         '<p class="subtitle">Omaha–Council Bluffs three-county study region</p>',
         '<div class="meta">Abhijith Reddy · EPA Smart Location Database v3 (2021 release)</div>',
         f'<div class="stats"><div class="stat"><strong>{N}</strong><span>Block groups in study area</span></div>'
         f'<div class="stat"><strong>{valid_jobs}</strong><span>With observed transit-job access</span></div>'
         f'<div class="stat"><strong>{n_flag}</strong><span>Relative gap screening candidates</span></div></div>',
         '<h2>Research question and main finding</h2>',
         '<p><strong>Question:</strong> How do households without a vehicle relate to transit service and transit-based access to employment?</p>',
         f'<div class="callout"><p><strong>Main finding.</strong> Among block groups with usable transit indicators, transit service generally appears concentrated in neighborhoods where car-free households are more common. Yet this regional pattern hides <strong>{n_flag} higher-car-free block groups with comparatively limited modeled transit access to employment</strong>. These locations are candidates for further investigation using current GTFS schedules, ridership and local service data, not confirmed transit deserts.</p></div>',
         '<h2>Methods</h2>',
         '<h3>Data source, scope and preparation</h3>',
         '<p>We analyze the team-filtered EPA Smart Location Database v3 (2021 release): Douglas and Sarpy counties in Nebraska and Pottawattamie County in Iowa. The sample includes areas beyond incorporated Omaha and Council Bluffs. Each row represents a census block group. The source data were filtered by county; the numeric access measures were parsed for analysis.</p>',
         '<p>The original <code>GEOID10</code> and <code>GEOID20</code> fields in the uploaded file are truncated/rounded. We reconstructed 12-digit <em>candidate</em> block-group IDs using <code>STATEFP</code>, <code>COUNTYFP</code>, <code>TRACTCE</code> and <code>BLKGRPCE</code>. The reconstructed IDs must be validated against authoritative boundaries before GIS joins or location-specific planning.</p>',
         '<h3>Indicator definitions</h3>',
         '<table><thead><tr><th>Field</th><th>Measure</th><th>Interpretation</th></tr></thead><tbody>',
         '<tr><td><code>Pct_AO0</code></td><td>Share of households with zero vehicles</td><td>Fraction converted to percentage for display</td></tr>',
         '<tr><td><code>D4A</code></td><td>Walking network distance to nearest qualifying transit stop</td><td>Lower means a closer stop, for observed records</td></tr>',
         '<tr><td><code>D4C</code></td><td>Afternoon peak-period transit-service frequency</td><td>Higher means greater reported frequency</td></tr>',
         '<tr><td><code>D4D</code></td><td>Transit-service frequency density</td><td>Higher means greater reported density</td></tr>',
         '<tr><td><code>D5BR</code></td><td>Decay-weighted jobs accessible by transit</td><td>Higher modeled access; not a literal count of all reachable jobs</td></tr>',
         '<tr><td><code>D5AR</code></td><td>Decay-weighted jobs accessible by auto</td><td>Different mode and time assumptions from D5BR</td></tr>',
         '</tbody></table>',
         '<h3>Missing-value handling and coverage rules</h3>',
         '<p>EPA sentinel <code>-99999</code> values are treated as <strong>unavailable, never as zero</strong>. Some such codes may reflect distance limits, incomplete GTFS inputs or other noncoverage rules. Each analysis uses only observed values for that particular indicator; denominators therefore differ. Missing transit values are <strong>not</strong> classified as weak transit service.</p>',
         f'<p>Only <strong>{valid_jobs} of {N}</strong> block groups have observed D5BR. In Pottawattamie County, just <strong>1 of 93</strong> have a valid D5BR value. Therefore, missing Iowa-side data cannot be used to infer no transit service or to support a direct Omaha–Council Bluffs transit-access comparison.</p>',
         '<h3>Correlations, medians and the higher-car-free threshold</h3>',
         f'<p>We use <strong>Spearman rank correlation</strong> to summarize monotonic associations between <code>Pct_AO0</code> and each accessibility measure, using complete pairs for each measure. The <strong>75th percentile</strong> of car-free household share across all {N} block groups is <strong>{cut*100:.2f}%</strong> ({n_hi} block groups at or above this cutoff). We compare each indicator’s observed medians for this higher-car-free group versus other block groups. These summaries are descriptive and are not causal estimates.</p>',
         '<h3>Relative-gap screening definition</h3>',
         f'<p>The screen flags a block group only if <strong>(1)</strong> zero-vehicle household share is at least <strong>{cut*100:.2f}%</strong> (full-sample upper quartile), and <strong>(2)</strong> observed transit employment access <code>D5BR</code> falls below <strong>{fmt(median_transit_jobs)}</strong>, the median across all measured D5BR values. A block group without D5BR data cannot be screened.</p>',
         '<p>This rule is a dataset-relative heuristic for prioritizing follow-up. It is <strong>not an official transit-service or planning standard</strong> and does not independently establish inadequate transit service.</p>',
         '<h2>Results</h2>',
         '<h3>Data coverage by county</h3>',
         '<table><thead><tr><th>County</th><th>Block groups</th><th>D4A observed</th><th>D4C observed</th><th>D5BR observed</th></tr></thead><tbody>',coverage_rows,'</tbody></table>',
         figure(1,'Transit-indicator coverage by county','01_coverage_by_county.png',
            f'Coverage is extremely uneven. D5BR is available for {valid_jobs} of {N} block groups, including only 1 of 93 in Pottawattamie County. These bars report <em>data availability</em>, not actual service supply.',
            'Incomplete and geographically imbalanced data can distort area comparisons or falsely suggest that unmeasured neighborhoods have no transit.',
            'Seek consistent current GTFS, service coverage and ridership data across both states before interpreting or ranking locations.',
            'Two sets of bars show the percentage of block groups with observed transit indicators for three counties.'),
         '<h3>Observed associations and descriptive group medians</h3>',
         '<table><thead><tr><th>Indicator</th><th>Observed n</th><th>Spearman ρ</th><th>Higher-car-free median</th><th>Other median</th></tr></thead><tbody>',comparison_rows,'</tbody></table>',
         f'<p>Car-free share has a positive association with transit job access (<strong>ρ = {comp["D5BR"].spearman_rho:+.3f}</strong>, n={comp["D5BR"].valid_n}), '
         f'with frequency (<strong>ρ = {comp["D4C"].spearman_rho:+.3f}</strong>, n={comp["D4C"].valid_n}) and a negative association with stop distance (<strong>ρ = {comp["D4A"].spearman_rho:+.3f}</strong>, n={comp["D4A"].valid_n}). Negative distance correlation indicates closer stops among observed records. Correlation does not imply causation.</p>',
         figure(2,'Car-free share and modeled transit access to jobs','02_carfree_vs_transit_jobs.png',
            'The overall trend is positive, but the flagged points at higher car-free shares and below-median transit-job access reveal important exceptions. The vertical axis is logarithmic; dashed lines mark screening thresholds.',
            'A favorable regional relationship can obscure smaller groups of neighborhoods that may be underserved relative to others with similar car-free reliance.',
            'Start with the flagged observations, then investigate transit connections to employment sites, frequency, transfer burden, and actual trip times.',
            'Scatterplot of car-free household share against decay-weighted transit-job accessibility with highlighted screening candidates.'),
         figure(3,'Car-free share and walk distance to a transit stop','03_carfree_vs_stop_distance.png',
            'Higher car-free shares generally coincide with shorter observed walk distances to qualifying transit stops, although the scatter shows substantial neighborhood variation.',
            'Stop proximity alone does not guarantee frequent, reliable service or practical access to employment.',
            'Review pedestrian access, stop accessibility, service frequency and travel-time connections, not just map distance.',
            'Scatterplot of car-free share against walking distance to a transit stop.'),
         figure(4,'Transit job access across car-free household groups','04_transit_jobs_by_group.png',
            f'The observed higher-car-free group has a median of <strong>{fmt(comp["D5BR"].higher_carfree_median)}</strong> weighted transit-accessible jobs, compared with <strong>{fmt(comp["D5BR"].other_median)}</strong> among other observed groups. Both distributions vary. Plot markers for outliers are hidden for readability, not excluded from the medians.',
            'A stronger typical outcome for one group does not rule out meaningful within-group access gaps.',
            'Combine distribution patterns with local travel needs and the flagged candidate list rather than planning from group medians alone.',
            'Boxplot comparing observed modeled transit-job accessibility for higher-car-free and other block groups.'),
         figure(5,'Modeled employment access by transit versus automobile','05_transit_vs_auto_jobs.png',
            f'The plot pairs observed transit-job access (D5BR) with auto-job access (D5AR). Transit values are observed for {valid_jobs} block groups, whereas D5AR is available for all {N}. The two indicators use different model assumptions.',
            'Values are not comparable as a literal percent of identical jobs reachable within the same door-to-door travel time.',
            'Use this to identify places needing closer analysis; for formal modal comparisons, calculate current door-to-door travel times under aligned assumptions.',
            'Scatterplot comparing modeled decay-weighted accessibility by car and transit.'),
         '<h3>Relative gap candidates: the actionable shortlist</h3>',
         f'<p><strong>{n_flag} of {hi_observed}</strong> higher-car-free block groups with measured transit-job scores ({n_flag/hi_observed*100:.1f}%) meet both screening conditions. They are <strong>candidates for investigation, not proven transit deserts</strong>. Ten with the lowest observed modeled transit-job scores are listed below; the full list is in <code>results/relative_gap_candidates.csv</code>.</p>',
         '<table><thead><tr><th>Reconstructed candidate ID</th><th>County</th><th>Car-free share</th><th>Weighted transit jobs</th><th>Walk distance (m)</th></tr></thead><tbody>',gap_rows,'</tbody></table>',
         '<p><strong>Why this matters.</strong> The shortlist makes the regional association operational: it directs attention to specific observed areas while recognizing that the screen does not measure official adequacy.</p>',
         '<p><strong>Planner next step.</strong> Verify block-group identifiers, refresh GTFS and ridership data, model current job trips, and consult transit users before considering service changes or capital investments.</p>',
         '<h2>Discussion, limitations and team integration</h2>',
         '<p><strong>Interpretation:</strong> Among observed block groups, transit service generally appears concentrated where car-free households are more common. Nonetheless, 47 higher-car-free block groups have comparatively limited <em>modeled</em> transit access to employment. The flag identifies opportunities for follow-up analysis, not confirmed service insufficiency.</p>',
         '<ul><li><strong>Nonrandom missingness.</strong> D5BR is observed for only 362/727 block groups and only 1/93 in Pottawattamie. Missing Iowa values do not imply zero transit service and must not be used for a direct Omaha–Council Bluffs transit comparison.</li>',
         '<li><strong>Geographic scope.</strong> The three-county area extends beyond Omaha and Council Bluffs city limits; reconstructed geographic IDs need validation before mapping.</li>',
         '<li><strong>Data vintage and modeled outcomes.</strong> The 2021 EPA release reflects historical data, not current 2026 routes, ridership or travel times; D5AR and D5BR differ in mode and timing assumptions.</li>',
         '<li><strong>Noncausal evidence.</strong> Differences may reflect income, density, land use and residential selection; correlations are not evidence that transit service caused vehicle-ownership patterns.</li>',
         '<li><strong>Team integration.</strong> Compare flags with Adithya’s neighborhood clusters and Juicio’s vehicle-ownership model. Noah’s cross-area comparison should explicitly state the severe transit-data coverage imbalance.</li></ul>',
         '<h2>Sources</h2>',
         '<ul><li><a href="https://www.epa.gov/smartgrowth/smart-location-mapping">U.S. EPA: Smart Location Mapping</a></li>',
         '<li><a href="https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1014W9I.TXT">U.S. EPA: Smart Location Database v3 Technical Documentation (2021)</a></li>',
         '<li>Team-filtered <code>EPA_SDL_OmahaCouncilBluffs.csv</code>, from EPA SLD v3.</li></ul>',
         '</main></body></html>']
html_doc=''.join(parts)
(ROOT/'Transit_Employment_Accessibility_Report.html').write_text(html_doc,encoding='utf-8')

# Embed exact generated PNGs for an independently viewable standalone HTML report.
import re as _re

def embed_image(match):
    fname=match.group(1)
    raw=(ROOT/'figures'/fname).read_bytes()
    return 'src="data:image/png;base64,'+base64.b64encode(raw).decode('ascii')+'"'
standalone=_re.sub(r'src="figures/([^"]+\.png)"',embed_image,html_doc)
(ROOT/'Transit_Employment_Accessibility_Report_Standalone.html').write_text(standalone,encoding='utf-8')

summary=(
    f'Total block groups: {N}\n'
    f'Car-free household share weighted by households: {weighted:.2f}%\n'
    f'Upper quartile car-free threshold (full sample): {cut*100:.2f}%\n'
    f'Higher-car-free block groups: {n_hi}\n'
    f'Observed transit job accessibility (D5BR): {valid_jobs}\n'
    f'High-car-free blocks with observed D5BR: {hi_observed}\n'
    f'Observed D5BR median (weighted jobs): {median_transit_jobs:,.0f}\n'
    f'Relative gap candidates: {n_flag}\n'
    f'Rho Pct_AO0 vs D5BR: {comp["D5BR"].spearman_rho:.3f}\n'
    f'Rho Pct_AO0 vs D4C: {comp["D4C"].spearman_rho:.3f}\n'
    f'Rho Pct_AO0 vs D4A: {comp["D4A"].spearman_rho:.3f}\n'
    f'Unique raw GEOID10 values: {df.GEOID10.nunique()} (unusable for exact block-group mapping)\n'
    f'Unique reconstructed IDs: {df.block_group_id_reconstructed.nunique()}\n'
)
(ROOT/'analysis_summary.txt').write_text(summary,encoding='utf-8')
print(summary)
print('Generated revised Methods/Results HTML, standalone HTML, 5 figures and 4 result tables in',ROOT)
