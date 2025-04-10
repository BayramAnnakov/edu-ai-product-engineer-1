"""
AppBot API Client

A client for interacting with the AppBot API to retrieve app review data and analytics.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import requests
from dotenv import load_dotenv

load_dotenv()


class AppBotClient:
    """
    Client for interacting with the AppBot API.
    """
    BASE_URL = "https://api.appbot.co/api/v2"

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the AppBot client.

        Args:
            username: AppBot API username/key. If not provided, will look for APPBOT_API_USERNAME env var.
            password: AppBot API password. If not provided, will look for APPBOT_API_PASSWORD env var.
        """
        self.username = username or os.environ.get("APPBOT_API_USERNAME")
        self.password = password or os.environ.get("APPBOT_API_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "API credentials must be provided either as arguments or environment variables "
                "(APPBOT_API_USERNAME and APPBOT_API_PASSWORD)."
            )

    def _request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the AppBot API.

        Args:
            endpoint: API endpoint to request.
            method: HTTP method (GET, POST, etc.)
            params: Query parameters.

        Returns:
            API response as a dictionary.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        auth = (self.username, self.password)

        try:
            response = requests.request(method, url, auth=auth, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"API Error: {e}")
            print(f"Response: {response.text}")
            raise

    def get_token_info(self) -> Dict:
        """
        Get information about the current API token.
        
        Returns:
            Dictionary containing token information.
        """
        return self._request("me")

    def get_apps(self) -> List[Dict]:
        """
        Get a list of apps associated with the team.
        
        Returns:
            List of app dictionaries.
        """
        response = self._request("apps")
        return response.get("results", [])

    def get_detected_languages(self) -> List[Dict]:
        """
        Get a list of detected languages.
        
        Returns:
            List of language dictionaries.
        """
        response = self._request("detected_languages")
        return response.get("results", [])

    def get_topics(self) -> List[Dict]:
        """
        Get a list of topics, custom topics & tags.
        
        Returns:
            List of topic dictionaries.
        """
        response = self._request("topics")
        return response.get("results", [])

    def get_countries(self, app_id: Union[int, str]) -> List[Dict]:
        """
        Get a list of review-specific countries for an app.
        
        Args:
            app_id: ID of the application.
            
        Returns:
            List of country dictionaries.
        """
        response = self._request(f"apps/{app_id}/countries")
        return response.get("results", [])

    def get_ratings_countries(self, app_id: Union[int, str]) -> List[Dict]:
        """
        Get a list of ratings-specific countries for an app.
        
        Args:
            app_id: ID of the application.
            
        Returns:
            List of country dictionaries.
        """
        response = self._request(f"apps/{app_id}/ratings_countries")
        return response.get("results", [])

    def get_reviews(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
        page: int = 1,
    ) -> Dict:
        """
        Get reviews for an app.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            page: Page number to fetch.
            
        Returns:
            Dictionary containing reviews and pagination info.
        """
        params = {"page": page}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/reviews", params=params)

    def get_review_summary_by_date(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
        pad_empty: bool = False,
        force_daily: bool = False,
    ) -> Dict:
        """
        Get review summary by date.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            pad_empty: Whether to return items for empty days.
            force_daily: Whether to prevent result from being aggregated over increasingly
                         large time periods based on supplied date range.
            
        Returns:
            Dictionary containing review summary by date.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
        
        params["pad_empty"] = "y" if pad_empty else "n"
        params["force_daily"] = "y" if force_daily else "n"
            
        return self._request(f"apps/{app_id}/reviews/by_date", params=params)

    def get_review_summary_by_country(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get review summary by country.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing review summary by country.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/reviews/by_country", params=params)

    def get_review_summary_by_stars(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get review summary by stars (rating).
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing review summary by stars.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/reviews/by_rating", params=params)

    def get_review_star_overview(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get review star overview.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing review star overview.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/reviews/overview", params=params)

    def get_sentiment_breakdown(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get sentiment breakdown.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing sentiment breakdown.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/sentiment/breakdown", params=params)

    def get_sentiment_timeline(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
        force_daily: bool = False,
    ) -> Dict:
        """
        Get sentiment timeline.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            force_daily: Whether to prevent result from being aggregated over increasingly
                         large time periods based on supplied date range.
            
        Returns:
            Dictionary containing sentiment timeline.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
        
        params["force_daily"] = "y" if force_daily else "n"
            
        return self._request(f"apps/{app_id}/sentiment/timeline", params=params)

    def get_versions(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get versions.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing versions.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/versions", params=params)

    def get_sentiment_grade(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get sentiment grade.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing sentiment grade.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/sentiment/grade", params=params)

    def get_words(
        self,
        app_id: Union[int, str],
        word_type: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get words by type.
        
        Args:
            app_id: ID of the application.
            word_type: Type of words to get (popular, critical, interesting, trending_up, 
                       trending_down, new).
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing words by type.
        """
        valid_word_types = ["popular", "critical", "interesting", "trending_up", "trending_down", "new"]
        if word_type not in valid_word_types:
            raise ValueError(f"word_type must be one of {valid_word_types}")
            
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/words/{word_type}", params=params)
        
    def get_popular_words(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Get popular words.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            Dictionary containing popular words.
        """
        return self.get_words(app_id, "popular", start, end, **kwargs)
        
    def get_critical_words(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Get critical words.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            Dictionary containing critical words.
        """
        return self.get_words(app_id, "critical", start, end, **kwargs)

    def get_phrases(
        self,
        app_id: Union[int, str],
        phrase_word_count: int,
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
    ) -> Dict:
        """
        Get phrases.
        
        Args:
            app_id: ID of the application.
            phrase_word_count: Number of words in the phrase (2, 3, or 4).
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            
        Returns:
            Dictionary containing phrases.
        """
        if phrase_word_count not in [2, 3, 4]:
            raise ValueError("phrase_word_count must be 2, 3, or 4")
            
        params = {"phrase_word_count": phrase_word_count}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/phrases", params=params)

    def get_app_topics(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
        include_all: bool = False,
    ) -> Dict:
        """
        Get app topics.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            include_all: Include custom topics and tags in output, as well as topics.
            
        Returns:
            Dictionary containing app topics.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
        
        params["include_all"] = "y" if include_all else "n"
            
        return self._request(f"apps/{app_id}/topics", params=params)

    def get_topic_reviews(
        self,
        app_id: Union[int, str],
        topic_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        keyword: Optional[str] = None,
        country: Optional[int] = None,
        sentiments: Optional[List[str]] = None,
        dlangs: Optional[List[str]] = None,
        version: Optional[str] = None,
        topic: Optional[int] = None,
        page: int = 1,
    ) -> Dict:
        """
        Get reviews for a topic.
        
        Args:
            app_id: ID of the application.
            topic_id: ID of the topic.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            keyword: Search term to filter results.
            country: ID of country to filter to.
            sentiments: List of sentiments to filter results (positive, neutral, negative, mixed).
            dlangs: List of detected languages to filter results.
            version: Version of app associated with review.
            topic: Topic, custom topic or tag ID to filter to.
            page: Page number to fetch.
            
        Returns:
            Dictionary containing topic reviews.
        """
        params = {"page": page}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if keyword:
            params["keyword"] = keyword
        if country:
            params["country"] = country
        if sentiments:
            params["sentiments"] = "+".join(sentiments)
        if dlangs:
            params["dlangs"] = "+".join(dlangs)
        if version:
            params["version"] = version
        if topic:
            params["topic"] = topic
            
        return self._request(f"apps/{app_id}/topics/{topic_id}/reviews", params=params)

    def get_ratings_live(
        self,
        app_id: Union[int, str],
        country: Optional[str] = None,
        resolve_to: Optional[str] = None,
    ) -> Dict:
        """
        Get live ratings.
        
        Args:
            app_id: ID of the application.
            country: iTunes country code or Google Play country code.
            resolve_to: (Google Play Only) Select between publicly or privately sourced datasets.
                        Valid values: self, private, public. Defaults to self.
            
        Returns:
            Dictionary containing live ratings.
        """
        params = {}
        
        if country:
            params["country"] = country
        if resolve_to:
            if resolve_to not in ["self", "private", "public"]:
                raise ValueError("resolve_to must be one of: self, private, public")
            params["resolve_to"] = resolve_to
            
        return self._request(f"apps/{app_id}/ratings", params=params)

    def get_ratings_historical(
        self,
        app_id: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        country: Optional[str] = None,
        resolve_to: Optional[str] = None,
    ) -> Dict:
        """
        Get historical ratings.
        
        Args:
            app_id: ID of the application.
            start: Start date in YYYY-MM-DD format. Defaults to 90 days ago.
            end: End date in YYYY-MM-DD format. Defaults to today.
            country: iTunes country code or Google Play country code.
            resolve_to: (Google Play Only) Select between publicly or privately sourced datasets.
                        Valid values: self, private, public. Defaults to self.
            
        Returns:
            Dictionary containing historical ratings.
        """
        params = {}
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if country:
            params["country"] = country
        if resolve_to:
            if resolve_to not in ["self", "private", "public"]:
                raise ValueError("resolve_to must be one of: self, private, public")
            params["resolve_to"] = resolve_to
            
        return self._request(f"apps/{app_id}/ratings/historical", params=params)

    def get_ratings_bulk(
        self,
        app_id: Union[int, str],
        start: str,
        next_page_token: Optional[str] = None,
        resolve_to: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict:
        """
        Get bulk ratings.
        
        Args:
            app_id: ID of the application.
            start: Start datetime in ISO8601 format.
            next_page_token: Token supplied by previous request to the same endpoint.
            resolve_to: (Google Play Only) Select between publicly or privately sourced datasets.
                        Valid values: self, private, public. Defaults to self.
            page_size: Number of datapoints per page (max 1000). Defaults to 20.
            
        Returns:
            Dictionary containing bulk ratings.
        """
        params = {"start": start, "page_size": page_size}
        
        if next_page_token:
            params["next_page_token"] = next_page_token
        if resolve_to:
            if resolve_to not in ["self", "private", "public"]:
                raise ValueError("resolve_to must be one of: self, private, public")
            params["resolve_to"] = resolve_to
            
        return self._request(f"apps/{app_id}/ratings/bulk", params=params)