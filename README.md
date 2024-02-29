# Docbridge

This is an **experimental** Object-Document Mapping library for MongoDB.
You can watch it being developed *live* on [MongoDB's YouTube channel](https://www.youtube.com/@MongoDB)!

## Mission Statement

* Managing large amounts of data in MongoDB while keeping a data schema flexible is challenging.
* This ODM is not an active record implementation, mapping documents in the database directly into similar objects in code.
* This ODM *is* designed to abstract underlying documents, mapping potentially multiple document schemata into a shared object representation.
* It should also simplify the evolution of documents in the database, automatically migrating individual documents' schemas either on-read or on-write.
* There should be "escape hatches" so that unforeseen mappings can be implemented, hiding away the implementation code behind hopefully reuseable components.

## What Does It Do?

The library currently doesn't interact directly with MongoDB - what it _does_ do is wrap BSON documents returned by [PyMongo] or [Motor].

For example, let's say you have a BSON document like this:

```python
user_data_bson = {'_id': ObjectId('657072b56731c9e580e9dd70'),
    'bio': 'Music conference able doctor degree debate. Participant usually above '
        'relate.',
    'birth_date': datetime.datetime(1999, 7, 6, 0, 0),
    'email': 'deanjacob@yahoo.com',
    'follower_count': 59,
    'full_name': 'Deborah White',
    'user_id': '4',
    'user_name': '@tanya15',
    'followers': [{'_id': ObjectId('657072b66731c9e580e9dda6'),
                'bio': 'Rich beautiful color life. Relationship instead win '
                       'join enough board successful.',
                'user_id': '58',
                'user_name': '@rduncan'},
               {'_id': ObjectId('657072b66731c9e580e9dd99'),
                'bio': 'Picture day couple democratic morning. Environment '
                       'manage opportunity option star food she. Occur imagine '
                       'population single avoid.',
                'user_id': '45',
                'user_name': '@paynericky'},
               ]}
```

You can define a wrapper for it like this:

```python
from docbridge import Document


class UserProfile(Document):
    pass
```

The wrapper doesn't currently do very much - it just makes the `dict` returned by PyMongo look more like a regular Python class:

```python
profile = UserProfile(user_data_bson, db=None)
print(repr(profile._id))  # ObjectId('657072b56731c9e580e9dd70')
print(repr(profile.user_id))  # "4"
```

The real power of the library (like with most [ODM]s) comes from attaching field definitions to the class, to transform the way data is looked up on the underlying document.

Here is how the `Field` class can be used to configure mappings to different field names in the underlying document, or to transform the data in the underlying field, to convert a string to an int:

```python
from docbridge import Document, Field


class UserProfile(Document):
    id = Field(field_name="_id")  # id maps to the _id doc field.
    user_id = Field(transform=int)  # user_id transforms the field value to an int


profile = UserProfile(user_data_bson, db=None)
print(repr(profile.id))  # ObjectId('657072b56731c9e580e9dd70')
print(repr(profile.user_id))  # 4 <- This is an int now!
print(
    repr(profile.follower_count)
)  # 59 <- You can still access other doc fields as attributes.
```

## Fallthrough Fields

There are other types of field, though.
FallthroughField is one of them.
It allows you to _try_ to look up a field by one name,
and if the field is missing,
it will try other names that it's been configured with.

**Note:** This field type will _probably_ disappear, as I may merge its
functionality into `Field`.

```python
from docbridge import Document, FallthroughField

class UserProfile(Document):
    # The `name` attribute will look up the "full_name" field,
    # and fall back to the "name" if it's missing.
    name = FallthroughField(
        field_names=[
            "full_name",  # v2
            "name",  # v1
        ]
    )

profile = UserProfile({"full_name", "Mark Smith"})
assert profile.name == "Mark Smith"  # Works

profile = UserProfile({"name", "Mark Smith"})
assert profile.name == "Mark Smith"  # Also works!
```

## The Subset Pattern

Some support already exists for abstracting [MongoDB Design Patterns][mongodb-patterns],
like the [Subset Pattern][subset].
The subset pattern preserves document size at a reasonable level by only embedding a subset of related data - for example, only the first 10 followers on a social media profile. The rest of the followers would be stored in their own collection, and loaded only when necessary.

```python
class Follower(Document):
    _id = Field(transform=str)

class Profile(Document):
        _id = Field(transform=str)
        followers = SequenceField(
            type=Follower,
            superset_collection="followers",
            # The following query will be executed on "followers" if the field
            # is iterated past the embedded follower subdocuments.
            superset_query=lambda ob: [
                {
                    "$match": {"user_id": ob.user_id},
                },
                {"$unwind": "$followers"},
                {"$replaceRoot": {"newRoot": "$followers"}},
            ],
        )

# Print all the profile's followers to the screen,
# including those in the followers collection:
profile = Profile(user_data_bson, db=test_db)
for follower in profile:
    print(follower.id)
```

# Live Streams on YouTube

I've been developing docbridge on YouTube. You can catch the live streams at 2pm GMT on Wednesdays, or you can view the recordings:

## Episode 1: Building a Simple Data Access Layer

Introducing my plans for the library, and building out the `Document` class, and the `Simple` and `Fallthrough` classes. (The latter two get renamed later to `Field` and `FallthroughField`)

[![Building a Simple Data Access Layer](https://img.youtube.com/vi/dXXkuLjjHBA/0.jpg)](https://www.youtube.com/watch?v=dXXkuLjjHBA)


## Episode 2: Testing and Publishing a Python Module

Writing some Pytest test fixtures that will run tests in a transaction, and roll back any changes to the database. Then (attempting to) publish my module to PyPI!

[![Testing and Publishing a Python Module](https://img.youtube.com/vi/X9QqA0alA8Q/0.jpg)](https://www.youtube.com/watch?v=X9QqA0alA8Q)

## Episode 3: Subsets & Joins - Part 1

Joins are a fundamental part of data modeling in MongoDB! This episode adds a field type for embedded arrays, and in the next episode it'll be extended to look up data in other collections!

[![Subsets & Joins: Part 1](https://img.youtube.com/vi/YvZeA_jvYrY/0.jpg)](https://www.youtube.com/watch?v=YvZeA_jvYrY)

## Episode 4: Subsets & Joins - Part 2

More metaprogramming to turn a sequence of items that is split across documents and collections into a single Python sequence.

[![Subsets & Joins: Part 2](https://img.youtube.com/vi/TJVLkVUUzGk/0.jpg)](https://www.youtube.com/watch?v=TJVLkVUUzGk)

## Episode 5: Updating Data - Part 1

It's all very well reading data from the database, but it's also nice to be able
to update it!

[![Updating Data - Part 1](https://img.youtube.com/vi/Ab_NmiKP2_w/0.jpg)](https://www.youtube.com/watch?v=Ab_NmiKP2_w)

## Episode 6: Updating Data - Part 2

It turns out there's quite a lot of work to record and replay updates.
Let's get on with it!

[![Updating Data - Part 2](https://img.youtube.com/vi/2kIrKr0n9WY/0.jpg)](https://www.youtube.com/watch?v=2kIrKr0n9WY)

## Episode 7: Updating Data - Part 3

It turns out there's quite a lot of work to record and replay updates.
Let's get on with it!

[![Updating Data - Part 3](https://img.youtube.com/vi/3bW8Zzm8dpE/0.jpg)](https://www.youtube.com/watch?v=3bW8Zzm8dpE)



[PyMongo]: https://pymongo.readthedocs.io/en/stable/
[Motor]: https://motor.readthedocs.io/en/stable/
[ODM]: https://www.mongodb.com/developer/products/mongodb/mongodb-orms-odms-libraries/
[subset]: https://www.mongodb.com/blog/post/building-with-patterns-the-subset-pattern
[mongodb-patterns]: https://www.mongodb.com/blog/post/building-with-patterns-a-summary