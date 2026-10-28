"""Copy reviewed, public aggregate outputs into the static explorer."""
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[3]
site = Path(__file__).resolve().parents[1]
output = root / 'population-access/output'
shutil.copytree(output / 'web', site / 'data/population', dirs_exist_ok=True)
review = site / 'population-review'
review.mkdir(exist_ok=True)
shutil.copy2(output / 'review.html', review / 'review.html')
shutil.copytree(output / 'figures', review / 'figures', dirs_exist_ok=True)
print('Packaged public demographic aggregates and review figures.')
