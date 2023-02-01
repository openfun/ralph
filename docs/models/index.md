Ralph can be considered versatile since at some point it is
log-content-agnostic: most commands will work as expected without transforming
logged events content or format.

But on the other side, Ralph is a tool dedicated to learning events processing
so we've implemented key features related to learning events validation and
conversion. For now, we mostly focus on two learning events standards: [Open
edX](https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/analytics.html)
and [xAPI](https://adlnet.gov/projects/xapi/).

Data validation and serialisation/de-serialisation are achieved using
[pydantics](https://pydantic-docs.helpmanual.io) models that are documented in
the following subsections:

- [Open edX events](./edx/)
- [xAPI events](./xapi/)
