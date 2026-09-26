from database import SessionLocal, engine, Base
import models


# Create database tables if they don't already exist
Base.metadata.create_all(bind=engine)

# Open a database session
db = SessionLocal()


# Add products only if no products exist
if not db.query(models.Product).first():

    db.add_all([
        models.Product(
            name="Sneakers",
            price=2499.0,
            stock=1
        ),
        models.Product(
            name="T-Shirt",
            price=599.0,
            stock=50
        )
    ])

    db.commit()

    print("Products seeded successfully.")

else:

    print("Products already exist. Skipping.")


# Close database connection
db.close()