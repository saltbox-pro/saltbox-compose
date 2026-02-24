#! /bin/bash
set -e

bin_dir="$(dirname "$(realpath --relative-to "$(pwd)" "$0")")"
declare -r output='ca.crt'
declare -r usage_str="
Obtain Salt.Box Docker Compose local authority certificate.

Creates '${output}' file in a current working directory. File may be
used to connect by HTTPS and to explore redis-salt DB.

Usage: ./bin/get_ca.sh [-h|--help] [--inject-into-firefox]

  --inject-into-firefox\t\tAdd obtained certificate file to Firefox (all existing profiles)\n\n"
firefox_dirs=(
  "${HOME}/.mozilla/firefox/"
  "${HOME}/.config/mozilla/firefox/"
)

firefox_flag=0

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -h|--help) printf "$usage_str" && exit 0 ;;
    --inject-into-firefox) firefox_flag=1 ;;
    *) err "Unknown option $i" ;;
  esac
done


function inject_into_firefox() {
  while IFS= read -r -d '' cert_db
  do
    cert_dir=$(dirname "$cert_db");
    echo "Inject '${output}' into '${cert_dir}'"
    certutil \
      -d "${cert_dir}" \
      -An 'Salt.Box local CA' \
      -t 'CT' \
      -i "./${output}"
  done < <(find "${firefox_dirs[@]}" -name 'cert*.db' -print0)
}

"${bin_dir}/sb-compose.sh" cp make-certs:/mnt/redis_certs/ca.crt "./${output}"

if [ $firefox_flag = 1 ]; then inject_into_firefox; fi
