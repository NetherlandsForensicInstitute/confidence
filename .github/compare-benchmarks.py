import json
from argparse import ArgumentParser
from glob import iglob
from itertools import chain, groupby
from operator import itemgetter

from tabulate import tabulate


def compare_benchmarks(benchmarks, old, new):
    for benchmark, python, by_commit in benchmarks:
        result_old, result_new = by_commit[old], by_commit[new]
        yield benchmark, python, (result_new - result_old) / result_old


def combine_runs(runs, commits):
    stats = sorted(chain.from_iterable(runs))
    for benchmark, by_python in groupby(stats, key=itemgetter(0)):
        for python, by_commit in groupby(by_python, key=itemgetter(1)):
            by_commit = {commit: value for *_, commit, value in by_commit if commit in commits}
            if len(by_commit) == len(commits):
                yield benchmark, python, by_commit


def read_run(run, stat='median'):
    python_implementation = run['machine_info']['python_implementation']
    python_version = '.'.join(run['machine_info']['python_version'].split('.')[:2])
    if python_implementation != 'CPython':
        python_version = f'{python_implementation} {python_version}'

    commit = run['commit_info']['id']

    for benchmark in run['benchmarks']:
        yield benchmark['name'], python_version, commit, benchmark['stats'][stat]


def loadf(f):
    with open(f, 'r') as f:
        return json.load(f)


def to_table(benchmarks):
    headers = None
    table = []

    for benchmark_name, by_python in groupby(benchmarks, key=itemgetter(0)):
        by_python = {python: difference for *_, python, difference in by_python}
        if not headers:
            headers = ('', *by_python.keys())

        table.append((benchmark_name, *by_python.values()))

    return headers, table


if __name__ == '__main__':
    args = ArgumentParser()
    args.add_argument('--old', metavar='COMMIT', required=True)
    args.add_argument('--new', metavar='COMMIT', required=True)
    args.add_argument('--stat', default='median')

    args = args.parse_args()

    benchmarks = (read_run(loadf(f), stat=args.stat) for f in iglob('.benchmarks/*/*.json'))
    benchmarks = combine_runs(benchmarks, commits={args.old, args.new})
    benchmarks = compare_benchmarks(benchmarks, old=args.old, new=args.new)
    headers, table = to_table(benchmarks)
    print(tabulate(table, headers=headers, tablefmt='github', floatfmt='+.0%'))
