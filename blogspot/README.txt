BlogSpot:
BlogSpot is a multi-user app used for creating Blogs or posts. Users should login to create or view posts.

Login / Register
	New users can Register using 'Register'. 
		User name and email should be unique.
		Password should be minimum of 8 characters.
		Users can upload image (available in static folder) as profile image.
	Existing users can login using username and password.

Home
	Users will be taken to the home page, where users can view the feeds. 
	The feeds are the posts created by other users, whom they follow.
	The feeds will be empty until user follow any other user.
	The feeds will be listed in the descending order of the post created / modified time.
		There will be facility to like, dislike or add / delete comments to a post.		
	The users profile page can be viewed by clicking on the username on the feed.

Create new post / blog
	User can create a post / blog using 'Create new post / blog' button.
		The title of the post should be unique.
		Users can upload image (available in static folder) as post image.

Search
	Users can search for other users by giving username.
	The matching users will be listed.
	Users can follow / unfollow another user using 'Follow' or 'Unfollow' button.
	The users profile page can be viewed by clicking on the username.

My Profile
	Displays the count of posts created by the user, 
	Displays count of the number of followers and number of following users.
	User can see the list of followers and following users by clicking on the count.
	Displays the posts created by the user descending order of the post created / modified time. 	
	Facility to edit and delete the post.

Export Posts
	Export posts option is available in 'My Profiles'.
	User can Export posts and comments to .csv file. The file will be saved into exports folder.

Update / Delete User Account
	This facility available in 'My Profile'.
	User can 'update personal details' or 'delete user account'
	Once the user account is deleted, all posts/comments added by the user will also gets deleted.

API
	Created APIs for CRUD on User, Posts. 
	APIs are available for view feeds, adding and deleting comments to a post.
	BlogSpotAPI.yaml file is created for testing API