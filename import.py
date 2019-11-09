import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import logging  
_logger = logging.getLogger(__name__)

# Set up database
engine = create_engine('postgresql://openpg:openpgpwd@localhost:5432/project1_db')
db = scoped_session(sessionmaker(bind=engine))
  
def main():
  f = open("books.csv")
  reader = csv.reader(f)
  count=0
  for isbn, title, author, year in reader:
      if count>=1:
          print(f"=== before books from isbn {isbn}, title {title}, author {author}, year {year}.")
          #   year = int(year)
          db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year}) # substitute values from CSV line into SQL command, as per this dict
          print(f"Added books from isbn {isbn}, title {title}, author {author}, year {year}.")
      count = count+1
    
  db.commit()
  
if __name__=="__main__":
    main()