# Docbridge

This is an experimental Object-Document Mapping library for MongoDB.
You can watch it being developed *live* on [MongoDB's YouTube channel](https://www.youtube.com/@MongoDB)!

## Mission Statement

* Managing large amounts of data in MongoDB while keeping a data schema flexible is challenging.
* This ODM is not an active record implementation, mapping documents in the database directly into similar objects in code.
* This ODM *is* designed to abstract underlying documents, mapping potentially multiple document schemata into a shared object representation.
* It should also simplify the evolution of documents in the database, automatically migrating individual documents' schemas either on-read or on-write.
* There should be "escape hatches" so that unforeseen mappings can be implemented, hiding away the implementation code behind hopefully reuseable components.
