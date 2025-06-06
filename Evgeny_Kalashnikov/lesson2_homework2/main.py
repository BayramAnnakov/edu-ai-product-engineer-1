import asyncio
from datetime import datetime
from pathlib import Path
from load_reviews import ReviewsLoader
from userboard_agents import ReviewAnalyzer, SolutionAnalyzer, UserPersonaAnalyzer, User
import random

async def generate_userboard_summary():
    # Initialize loaders and analyzers
    loader = ReviewsLoader()
    loader.load_data()
    
    review_analyzer = ReviewAnalyzer()
    solution_analyzer = SolutionAnalyzer()
    user_persona_analyzer = UserPersonaAnalyzer()
    
    # Get random product with reviews
    product_id = loader.get_random_product_with_reviews(50, 100)
    if not product_id:
        print("No suitable product found with the specified number of reviews.")
        return
    
    # Get product reviews
    product_reviews = loader.get_reviews_for_product(product_id)
    if not product_reviews:
        print(f"No reviews found for product {product_id}")
        return
    
    # Analyze product reviews
    print("Analyzing product reviews...")
    review_analysis = await review_analyzer.analyze_reviews(product_reviews)
    
    # Get users who reviewed this product
    users_df = loader.get_users_for_product(product_id, num_users=5)
    if users_df is None or len(users_df) == 0:
        print(f"No users found for product {product_id}")
        return
    
    # Create user agents
    users = []
    print(f"Creating user agents for {len(users_df)} users...")
    for i, (_, user_row) in enumerate(users_df.iterrows(), 1):
        user_id = user_row['UserId']
        user_reviews = loader.get_reviews_for_user(user_id)
        if user_reviews:
            user_profile = await user_persona_analyzer.analyze_user_persona(user_reviews)
            users.append(User(f"User_{i}_{user_id}", user_profile))
    
    # Generate solutions for top issues
    solutions = []
    print(f"Generating solutions for {len(review_analysis.top_issues)} issues...")
    for issue in review_analysis.top_issues:
        solution = await solution_analyzer.propose_solution(review_analysis.summary, issue)
        solutions.append((issue, solution))
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_{timestamp}.txt"
    
    # Write summary to file
    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("USER BOARD SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("-" * 40 + " PRODUCT INFORMATION " + "-" * 40 + "\n")
        f.write(f"Product ID: {product_id}\n")
        review_count = len([r for r in product_reviews.split('\n') if r.strip()])
        f.write(f"Number of Reviews: {review_count}\n\n")
        
        f.write("-" * 40 + " PRODUCT SUMMARY " + "-" * 40 + "\n")
        f.write(review_analysis.summary)
        f.write("\n\n")
        
        f.write("-" * 40 + " TOP ISSUES " + "-" * 40 + "\n")
        for issue in review_analysis.top_issues:
            f.write(f"• {issue}\n")
        f.write("\n")
        
        f.write("-" * 40 + " USER PROFILES " + "-" * 40 + "\n")
        for i, user in enumerate(users, 1):
            f.write(f"\nUser {user.agent.name}:\n")
            f.write("~" * 20 + "\n")
            f.write(f"Profile: {user.agent.instructions.split('This is how you have been described:')[1].split('Act naturally')[0].strip()}\n")
            f.write("~" * 20 + "\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("DISCUSSION\n")
        f.write("=" * 80 + "\n\n")
        
        for issue, solution in solutions:
            f.write("-" * 40 + f" ISSUE: {issue} " + "-" * 40 + "\n")
            f.write(f"Proposed Solution: {solution}\n\n")
            f.write("User Responses:\n")
            f.write("-" * 20 + "\n")
            
            for user in users:
                # Get user's response
                response = await user.respond(f"What do you think about this solution for the issue: {issue}?")
                if not response:
                    continue
                    
                f.write(f"{user.agent.name}: {response}\n")
                
                # Handle reactions to this response
                current_responder = user
                current_response = response
                reaction_count = 0
                remaining_users = [u for u in users if u != current_responder]
                
                while reaction_count < 3 and remaining_users:
                    # Get a random user to react
                    reacting_user = random.choice(remaining_users)
                    reaction = await reacting_user.react(f"What do you think about this solution for the issue: {issue}?", current_response)
                    
                    if reaction and reaction.lower().strip() not in ["none", "no follow-up", "n/a", "no", "not", "no follow up", "no follow-up", ""]:
                        f.write("  └─ " + f"{reacting_user.agent.name} (reacting to {current_responder.agent.name}): {reaction}\n")
                        current_responder = reacting_user
                        current_response = reaction
                        reaction_count += 1
                        # Reset remaining users for next reaction
                        remaining_users = [u for u in users if u != current_responder]
                    else:
                        # Remove user if they don't want to react
                        remaining_users.remove(reacting_user)
                        # If no reaction, don't count it towards the reaction limit
                        continue
                
                f.write("-" * 20 + "\n")
            
            f.write("\n")

if __name__ == "__main__":
    asyncio.run(generate_userboard_summary()) 