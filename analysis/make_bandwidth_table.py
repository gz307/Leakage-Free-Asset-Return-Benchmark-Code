from pathlib import Path
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tables', default='tables')
    args = parser.parse_args()
    folder = Path(args.tables)
    frame = pd.read_csv(folder / 'table6_bandwidth.csv')
    cols = ['Asset', 'Model', 'p_dMSE_lag1', 'p_dMSE_holm', 'p_dMSE_auto', 'p_dMSE_auto_holm']
    result = frame[cols].copy()
    result['sig_dMSE_holm'] = result.p_dMSE_holm < .05
    result['sig_dMSE_auto_holm'] = result.p_dMSE_auto_holm < .05
    result.to_csv(folder / 'table7.csv', index=False, float_format='%.12g')
    changed = result[result.sig_dMSE_holm != result.sig_dMSE_auto_holm]
    print(changed.to_string(index=False))

if __name__ == '__main__':
    main()
