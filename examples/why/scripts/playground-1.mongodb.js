// Playground
use('why');

profiles = db.getCollection("profiles");
followers = db.getCollection("followers");

profiles.find({ "user_id": "4" })