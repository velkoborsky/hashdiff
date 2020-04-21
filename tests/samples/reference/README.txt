Generating reference outputs with:
> find ../basic -type f -exec sh -c 'sha512sum -z {} | cut -c1-128 | tr -d "\n"' \; -printf '\t%s\t%C@\t%P\n' > basic.ref
