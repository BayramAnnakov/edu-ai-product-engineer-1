import pandas as pd
from pathlib import Path

class ReviewsLoader:
    def __init__(self, file_path: str = "../Reviews.csv"):
        """
        Initialize the ReviewsLoader with the path to the CSV file.
        
        Args:
            file_path (str): Path to the Reviews.csv file
        """
        self.file_path = Path(file_path)
        self.data = None
        
    def load_data(self) -> pd.DataFrame:
        """
        Load the reviews data from CSV file.
        
        Returns:
            pd.DataFrame: DataFrame containing the reviews data
        """
        try:
            self.data = pd.read_csv(self.file_path)
            print(f"Successfully loaded {len(self.data)} reviews")
            return self.data
        except FileNotFoundError:
            print(f"Error: File not found at {self.file_path}")
            return None
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None
            
    def get_data(self) -> pd.DataFrame:
        """
        Get the loaded reviews data.
        
        Returns:
            pd.DataFrame: DataFrame containing the reviews data
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
        return self.data

    def get_most_reviewed_product(self) -> str:
        """
        Get the product ID with the highest number of reviews.
        
        Returns:
            str: Product ID with the most reviews
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
            
        # Count reviews per product and get the one with maximum count
        product_review_counts = self.data['ProductId'].value_counts()
        most_reviewed_product = product_review_counts.idxmax()
        return most_reviewed_product

    def get_reviews_for_product(self, product_id: str) -> str:
        """
        Get all reviews for a specific product ID, combining summary and text fields.
        
        Args:
            product_id (str): The product ID to get reviews for
            
        Returns:
            str: Combined summary and text for all reviews
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
            
        # Filter reviews for the given product ID
        product_reviews = self.data[self.data['ProductId'] == product_id]
        
        if len(product_reviews) == 0:
            print(f"No reviews found for product ID: {product_id}")
            return None
            
        # Get unique reviews by combining Summary and Text
        unique_reviews = product_reviews.drop_duplicates(subset=['Summary', 'Text'])
        
        # Combine summary and text for each review
        combined_reviews = ""
        for _, review in unique_reviews.iterrows():
            combined_text = f"{review['Summary']}: {review['Text']}\n\n"
            # Check if adding this review would exceed token limit
            if len(combined_reviews) + len(combined_text) > 30000:
                print(f"Warning: Review text exceeds 30000 tokens, truncating...")
                break
            combined_reviews += combined_text
            
        return combined_reviews

    def get_reviews_for_user(self, user_id: str) -> str:
        """
        Get all reviews written by a specific user, combining summary and text fields.
        
        Args:
            user_id (str): The user ID to get reviews for
            
        Returns:
            str: Combined summary and text for all reviews by the user
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
            
        # Filter reviews for the given user ID
        user_reviews = self.data[self.data['UserId'] == user_id]
        
        if len(user_reviews) == 0:
            print(f"No reviews found for user ID: {user_id}")
            return None
            
        # Get unique reviews by combining Summary and Text
        unique_reviews = user_reviews.drop_duplicates(subset=['Summary', 'Text'])
        
        # Combine summary and text for each review
        combined_reviews = ""
        for _, review in unique_reviews.iterrows():
            combined_text = f"{review['Summary']}: {review['Text']}\n\n"
            # Check if adding this review would exceed token limit
            if len(combined_reviews) + len(combined_text) > 30000:
                print(f"Warning: Review text exceeds 30000 tokens, truncating...")
                break
            combined_reviews += combined_text
            
        return combined_reviews

    def get_users_for_product(self, product_id: str, num_users: int = 10) -> pd.DataFrame:
        """
        Get information about users who reviewed a specific product.
        
        Args:
            product_id (str): The product ID to get users for
            num_users (int): Maximum number of users to return (default: 10)
            
        Returns:
            pd.DataFrame: DataFrame containing user information for the product reviews
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
            
        # Filter reviews for the given product ID
        product_reviews = self.data[self.data['ProductId'] == product_id]
        
        if len(product_reviews) == 0:
            print(f"No reviews found for product ID: {product_id}")
            return None
            
        # Get unique users and their review counts
        user_stats = product_reviews.groupby('UserId').agg({
            'Score': 'mean',
            'HelpfulnessNumerator': 'sum',
            'HelpfulnessDenominator': 'sum'
        }).reset_index()
        
        # Sort by helpfulness (if denominator > 0)
        user_stats['HelpfulnessRatio'] = user_stats.apply(
            lambda x: x['HelpfulnessNumerator'] / x['HelpfulnessDenominator'] 
            if x['HelpfulnessDenominator'] > 0 else 0, 
            axis=1
        )
        
        # Sort by helpfulness ratio and score, then limit to num_users
        result = user_stats.sort_values(
            by=['HelpfulnessRatio', 'Score'], 
            ascending=[False, False]
        ).head(num_users)
        
        return result

    def get_random_product_with_reviews(self, min_reviews: int = 50, max_reviews: int = 100) -> str:
        """
        Get a random product ID that has between min_reviews and max_reviews.
        
        Args:
            min_reviews (int): Minimum number of reviews (default: 50)
            max_reviews (int): Maximum number of reviews (default: 100)
            
        Returns:
            str: Product ID with reviews in the specified range
        """
        if self.data is None:
            print("Data not loaded yet. Call load_data() first.")
            return None
            
        # Count reviews per product
        product_review_counts = self.data['ProductId'].value_counts()
        
        # Filter products with reviews in the specified range
        filtered_products = product_review_counts[
            (product_review_counts >= min_reviews) & 
            (product_review_counts <= max_reviews)
        ]
        
        if len(filtered_products) == 0:
            print(f"No products found with reviews between {min_reviews} and {max_reviews}")
            return None
            
        # Select a random product from the filtered list
        random_product = filtered_products.sample(1).index[0]
        return random_product

