#!/bin/bash
# Run from the reviewed package checkout on the Mac.
set -euo pipefail
umask 077
export GH_HOST=github.com
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -I "${script_dir}/publish_meteoswiss_836_beta.py" "$@"
