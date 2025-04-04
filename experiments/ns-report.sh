#! /bin/bash

opt_echo=false
opt_debug=false
opt_test=false
opt_verbose=false
opt_outdir="."

while [[ $# -gt 0 ]]; do
    case "$1" in
        --outdir)  opt_outdir="$2"; shift 2 ;;
        --debug)   opt_debug=true; shift ;;
        --echo)    opt_echo=true; shift ;;
        --test)    opt_debug=test; shift ;;
        --verbose) opt_verbose=true; shift ;;
        *)         echo "Unknown argument: $1"; exit 1 ;;
    esac
done

today=`date +"%Y-%m-%d"`

export VAULT_ADDR="https://something-something-prod.blargo.com"
export VAULT_TOKEN="1234"

env PYTHONIOENCODING=utf8 python3 ../vgr.py \
    --debug=${opt_debug} --echo=${opt_echo} --verbose=${opt_verbose} \
    "test=${opt_test}" \
    "outdir=${opt_outdir}" \
    "today=${today}" \
    "outdir=${opt_outdir}" \
<<EOF || echo "FAILED"

Assert env.VAULT_ADDR : "VAULT_ADDR not defined in environment"
Assert env.VAULT_TOKEN : "VAULT_TOKEN not defined in environment"

Set vault_env = env.VAULT_ADDR.RegexReplace("[.].*$").RegexReplace("^.*-").Upper().StrReplace("PROD", "Prod").StrReplace("DEV", "Dev")
Set report_title = "Vault Namespace"
Set fn = arg.outdir + "/" + arg.today + " - " + vault_env + " {}.{}"
Set log_fn = fn.format(arg.report_title + " Log", "txt")
Set csv_fn = fn.format(arg.report_title, "csv")
Set md_fn  = fn.format(arg.report_title, "md")
Set sid_fn = fn.format("SYSIDs", "csv")

# print "ross.Virosko@CITIZENSBANK.com".Split("@", 2).Stash(_.mail).Item(0).TitleCase() + "@" + _.mail.Item(1).Lower()


EOF
