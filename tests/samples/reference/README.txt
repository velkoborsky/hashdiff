Generating reference outputs with (e.g.):
> find ../basic -type f -exec sh -c 'sha512sum -z {} | cut -c1-128 | tr -d "\n"' \; -printf '\t%s\t%T@\t%P\n' > basic.ref
