# trust_net.py: core logic with timezone-aware datetimes
import networkx as nx
from enum import Enum
from typing import Any, Dict, List, Optional
import datetime
import math

class NodeType(Enum):
    USER = 'User'
    PROFESSIONAL = 'Professional'
    SERVICE = 'ServiceInteraction'
    FEEDBACK = 'Feedback'

class RelationshipType(Enum):
    USER_SERVICE = 'requested'
    SERVICE_PROFESSIONAL = 'provided'
    SERVICE_FEEDBACK = 'has_feedback'
    USER_USER = 'connected'

class NetworkOfTrust:
    def __init__(self,
                 weight_baseline: float = 0.1,
                 weight_avg_ratings: float = 0.3,
                 weight_volume: float = 0.1,
                 weight_recency: float = 0.2,
                 weight_sentiment: float = 0.2,
                 weight_variance: float = 0.1,
                 decay_half_life_days: float = 30.0):
        self._graph = nx.DiGraph()
        self.weights = {
            'baseline': weight_baseline,
            'avg_ratings': weight_avg_ratings,
            'volume': weight_volume,
            'recency': weight_recency,
            'sentiment': weight_sentiment,
            'variance': weight_variance
        }
        self.decay_half_life = decay_half_life_days

    def _current_time(self) -> datetime.datetime:
        # Use timezone-aware UTC
        return datetime.datetime.now(datetime.timezone.utc)

    def clear(self):
        self._graph.clear()

    def _decay_weight(self, feedback_date: datetime.datetime) -> float:
        delta = self._current_time() - feedback_date
        days = delta.total_seconds() / 86400.0
        return 2 ** (- days / self.decay_half_life)

    def add_user(self, user_id: str, name: str = None, location: str = None, preferences: Dict[str, Any] = None):
        self._graph.add_node(user_id, type=NodeType.USER, name=name,
                              location=location, preferences=preferences or {})

    def add_professional(self, prof_id: str, name: str = None,
                         specializations: List[str] = None,
                         service_area: str = None, contact: str = None,
                         baseline_trust: float = 0.0):
        self._graph.add_node(prof_id, type=NodeType.PROFESSIONAL, name=name,
                              specializations=specializations or [],
                              service_area=service_area,
                              contact=contact,
                              baseline_trust=baseline_trust)

    def add_service_interaction(self, service_id: str, user_id: str,
                                prof_id: str, service_type: str,
                                date: Optional[str] = None,
                                status: str = 'Completed'):
        date = date or self._current_time().isoformat()
        self._graph.add_node(service_id, type=NodeType.SERVICE,
                              user_id=user_id, prof_id=prof_id,
                              service_type=service_type, date=date,
                              status=status)
        self._graph.add_edge(user_id, service_id, type=RelationshipType.USER_SERVICE)
        self._graph.add_edge(service_id, prof_id, type=RelationshipType.SERVICE_PROFESSIONAL)

    def add_feedback(self, feedback_id: str, service_id: str,
                     overall_rating: float,
                     specific_ratings: Dict[str, float],
                     review_text: str,
                     feedback_date: Optional[str] = None,
                     processed_attrs: Dict[str, Any] = None):
        feedback_date = feedback_date or self._current_time().isoformat()
        self._graph.add_node(feedback_id, type=NodeType.FEEDBACK,
                              overall_rating=overall_rating,
                              specific_ratings=specific_ratings,
                              review_text=review_text,
                              feedback_date=feedback_date,
                              processed_attrs=processed_attrs or {})
        self._graph.add_edge(service_id, feedback_id, type=RelationshipType.SERVICE_FEEDBACK)

    def compute_trust_score(self, prof_id: str, seeking_user_id: str) -> float:
        node = self._graph.nodes[prof_id]
        baseline = node.get('baseline_trust', 0.0)

        ratings = []
        for service in self._graph.predecessors(prof_id):
            if self._graph.nodes[service]['type'] == NodeType.SERVICE:
                for fb in self._graph.successors(service):
                    data = self._graph.nodes[fb]
                    if data['type'] == NodeType.FEEDBACK:
                        dt = datetime.datetime.fromisoformat(data['feedback_date'])
                        # ensure dt is timezone-aware
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=datetime.timezone.utc)
                        ratings.append({
                            'overall': data['overall_rating'],
                            'specific': data['specific_ratings'],
                            'date': dt,
                            'sentiment': data['processed_attrs'].get('sentiment', 0.0)
                        })
        n = len(ratings)
        vol_score = math.log(n + 1)
        if n == 0:
            return baseline

        crit_vals = {}
        for fb in ratings:
            for c, v in fb['specific'].items(): crit_vals.setdefault(c, []).append(v)
        avg_quant = sum(sum(vs)/len(vs) for vs in crit_vals.values())/len(crit_vals) if crit_vals else 0.0

        wsum = sum(fb['overall'] * self._decay_weight(fb['date']) for fb in ratings)
        wtot = sum(self._decay_weight(fb['date']) for fb in ratings)
        recency = wsum/wtot if wtot else 0.0

        sent = sum(fb['sentiment'] for fb in ratings)/n
        mean_ov = sum(fb['overall'] for fb in ratings)/n
        var = sum((fb['overall']-mean_ov)**2 for fb in ratings)/n

        w = self.weights
        variance_penalty = 1.0 if var < 0.1 else 0.0 # penalize variance (= too many reviews in a short time)
        temporal_penalty = 0.5 if self.detect_temporal_clustering(ratings) else 0.0
        return (w['baseline']*baseline + w['avg_ratings']*avg_quant +
                w['volume']*vol_score + w['recency']*recency +
                w['sentiment']*sent - w['variance']*variance_penalty - temporal_penalty)

    def recommend_professionals(self, seeking_user_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
        pros = [n for n,a in self._graph.nodes(data=True) if a['type']==NodeType.PROFESSIONAL]
        scored = [(p, self.compute_trust_score(p, seeking_user_id)) for p in pros]
        return [{'professional_id':p,'trust_score':s} for p,s in sorted(scored,key=lambda x:x[1],reverse=True)[:top_n]]

    def detect_temporal_clustering(self, ratings, threshold_days=1.0, max_allowed=3):
        timestamps = [fb['date'] for fb in ratings]
        timestamps.sort()
        count = sum(1 for i in range(len(timestamps)-1)
                    if (timestamps[i+1] - timestamps[i]).total_seconds() / 86400.0 < threshold_days)
        return count > max_allowed  # True se ci sono troppi feedback ravvicinati