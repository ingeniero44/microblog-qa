from app import create_app, db 
a = create_app() 
a.app_context().push() 
db.create_all() 
print("BD lista") 
