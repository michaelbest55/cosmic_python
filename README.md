This repository was used to go through the
[cosmic python book](https://www.cosmicpython.com). I have been through most of the tdd book the author had written previously, and thought I would work through this once since we use DDD in some of the projects I am working for at work.


Notes to self:
At the end of chapter two, I've gotten to a place where mypy complains about id
not being an attriute of Batch, which is true for the domain model, but not for
the SqlAlchemy model. How to fix this other than ignoring it? The alternative
was to add id to both of the models only as a type, but then we get implementation
details from the database into the domain model code, which is why for now I have
ignored the mypy error.


## Setup
Make a copy of example.env to .env.

```bash
poetry export -f requirements.txt --without-hashes | sed  's/;.*//g' > requirements.txt
```
