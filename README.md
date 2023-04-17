# Make a prediction

This code contains Python functions that interact with the Luno API to download candlestick data for a given currency pair ('XBTZAR' is the default), clean and process the data, generate lagged features, make a prediction using a pre-trained model, and return a DataFrame of the cleaned and lagged data along with a DataFrame of derivatives.

The cleaning() function is responsible for downloading, cleaning and processing the data, while the accounting() function retrieves account balance data from the Luno API. Finally, the post_market_order() function places a market order with Luno's API using a pre-trained model's prediction.

The code also imports various libraries, including numpy, pandas, joblib, dotenv, requests, and time. The load_dotenv() function is used to load environment variables, and getenv() is used to retrieve them.

# Create a model

## This code performs the following steps:

- Imports necessary libraries such as pandas, numpy, scikit-learn's train_test_split, logistic regression, GridSearchCV, and joblib.
- Reads a csv file ('assets/model.csv') into a pandas DataFrame object called "candles" and drops the first column 'Unnamed: 0'.
- Removes duplicate rows in the DataFrame using the drop_duplicates() method.
- Converts columns in the "candles" DataFrame to the appropriate data types (float for numeric columns, bool for the "signal" column).
- Splits the DataFrame into independent variables (ind_vars) and dependent variable (dep_vars).
- Splits the independent and dependent variables into training and testing sets using train_test_split() method.
- Performs a grid search to find the best hyperparameters for logistic regression using GridSearchCV.
- Fits the logistic regression model on the training set using the best hyperparameters found in the previous step.
- Prints the accuracy score of the model on the test set.
- Saves the trained model as a pickle file ('assets/model.pkl') using joblib.dump() method.

# app.py

This code defines a Flask API that provides various endpoints to access and manipulate data related to a financial model. The endpoints are:

/transaction/: Returns the description of the first transaction from an accounting module.
/bal/<string:asset>/: Returns the balance of a given asset from an accounting module.
/candles/<string:pair>/: Returns a dictionary containing candlestick data for a given trading pair after cleaning the data using a cleaning() function.
/derives/<string:pair>/<string:deriv>/: Returns the value of a given derivative of a given trading pair after cleaning the data using a cleaning() function.
/model/download/: Allows users to download the financial model saved as a model.pkl file located in the assets' folder.
/: Returns a simple greeting message, "Hello from Model Server API".
The code also imports the getenv function from the os module and the Flask and send_file functions from the flask module. It sets up the Flask application and initializes an accounting module by calling the accounting() function. Finally, it runs the Flask application if the script is run directly.

# Do analyses

This code reads in a CSV file called 'data.csv' located in a folder called 'assets' and performs several data processing tasks on the data. The processed data is then saved as a new CSV file called 'model.csv' in the same folder.

## The data processing tasks performed include:

- Creating three new columns called 'tminus_1', 'tminus_2', and 'tminus_3' which contain the lagged price changes from the previous 1, 2, and 3 time periods, respectively. Similarly, it also creates columns called 'vol_1', 'vol_2', and 'vol_3' which contain the lagged volumes from the previous 1, 2, and 3 time periods, respectively.
- Renaming the 'timestamp' column to 'Time' and setting it as the index.
- Dropping duplicate rows.
- Converting the 'open', 'close', 'high', 'low', and 'volume' columns to floats.
- Creating a new column called 'change' which contains the percent change in closing price from the previous time period.
- Creating a list of column names for the lagged price changes and volumes.
- Creating a new column called 'ema12' which contains the exponential moving average of the closing price over the past 12 time periods.
- Creating a new column called 'ema12_diff' which contains the percent change in the exponential moving average compared to the closing price. It is lagged by one time period.
- Dropping rows with missing values.
- Creating a new column called 'signal' which is True if the price change is positive and False otherwise.
- Finally, the processed data is saved as a new CSV file called 'model.csv' in the same 'assets' folder.