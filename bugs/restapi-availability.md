I noticed I have to start the writer _after_ LMU has started, otherwise the call to the rest-api fails and we fallback to using only the shared memory api.

I think we should:

- detect the process
- _then_ try the rest-api (if we don't already have what we need, or its >24hrs old for example)
- if the rest-api call fails, we could try again later, eg: when ready to save a file

we could also check for "unenriched" csv files and enrich them, if we successfully manage to reach the rest-api. I don't know what a good trigger for that would be, we could raise another bug for it if its better dealt with seperately.
