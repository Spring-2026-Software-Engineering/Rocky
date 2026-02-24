Api key generation demo
Makes a key under sk_kent_(key) then stores its hash into a db.json file. I also added a 12 hour timeout to the keys which can be changed but after 12 hours the key dies. 
To test this start with 
1. ```npm install``` in terminal
2. ```npx ts-node api-key-thing.ts generate``` to generate the key and store the hash in a db.json file
3. finally copy the given key and use ```npx ts-node api-key-thing.ts validate sk_kent_(your_key_here)``` gives you a access granted if it worked or access denied just for now and gives you your id and time created/expires.
