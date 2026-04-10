from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd

# Load the datasets
movies = pd.read_csv('movie.csv')
ratings = pd.read_csv('ratings.csv')

print("Movies:")
print(movies.head())  # Show only the first few rows for clarity
print("\nRatings:")
print(ratings.head())  # Show only the first few rows for clarity

# Create a user-item matrix
# Create a user-item matrix
user_item_matrix = ratings.pivot_table(index='userId', columns='movieId', values='rating').fillna(0)
print("\nUser-Item Matrix:")
print(user_item_matrix.head())  # Show only the first few rows for clarity


# Fit the k-NN model
knn = NearestNeighbors(n_neighbors=2, metric='cosine')
knn.fit(user_item_matrix)

# Example: Find similar users for UserID 1
user_id = 1
if user_id in user_item_matrix.index:
    distances, indices = knn.kneighbors(user_item_matrix.loc[user_id].values.reshape(1, -1))

    print("\nSimilar Users:")
    for i in range(len(distances.flatten())):
        if i == 0:
            continue  # Skip the user itself
        print(f"User {user_item_matrix.index[indices.flatten()[i]]} (Distance: {distances.flatten()[i]:.2f})")

    # Get recommendations for UserID 1
    similar_user_id = user_item_matrix.index[indices.flatten()[1]]
    similar_user_ratings = user_item_matrix.loc[similar_user_id]

    print("\nRecommendations for User 1:")
    recommended_movie_ids = similar_user_ratings[similar_user_ratings > 0].index
    recommendations = movies[movies['movieId'].isin(recommended_movie_ids)]

    print(recommendations)
else:
    print(f"UserID {user_id} not found in the user-item matrix.")
