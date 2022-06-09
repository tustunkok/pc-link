import subprocess


def latest_commit_hash(request):
    latest_commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True)
    return { 'latest_commit': latest_commit }