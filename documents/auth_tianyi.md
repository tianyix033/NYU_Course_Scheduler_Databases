## What I did
Implemented the authentication feature with a /auth/login and /auth/register.
You can find screenshots of successful local testings 
Feel free to test and report any bugs.

## How to test
Download postgresql. Set a password for yourself and memorize it. Create a file named .env in your project repo with the following contents:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=whatever your password is
DB_NAME=course_planner
FLASK_SECRET_KEY=a random key; should be around 32+ byte long and random;
```
Absolutely do not commit the above file or its contents.
The service starts automatically, but you would need to run setup_database.py do populate the database. Then run python app.py to start the application. Finally, open your browser and go to localhost:5000 and you should see the app.

## Next step
I'm expecting the /courses route to be finished before we can move on to implement the homepage and other pages including the reviews and schedules.
Create a branch and develop on that branch; then create a pull request so that others can view
your code before merging it.
If you have any doubts, you can reference my code or ask me directly. To put it simply, the routing (backend) is handled by the python scripts which specifies what to do for get/post requests at each route.
The actual pange (frontend) is handled by the html files in ./templates. I used Pico.css (v2) loaded from the jsDelivr CDN, which is a lightweight CSS framework that provides clean default styling so basic HTML elements look polished without custom CSS. 