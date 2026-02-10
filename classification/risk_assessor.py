class RiskAssessor:
    @staticmethod
    def calculate_risk(probabilities, contextual_risk_factors=0):
        """
        Determines risk level based on classification probabilities and historical context.
        
        probabilities: dict of {Class: Score}
        contextual_risk_factors: Integer count of keywords like 'suicide', 'hurt', etc. in recent history.
        """
        
        depression_score = probabilities.get("Depression", 0)
        anxiety_score = probabilities.get("Anxiety", 0)
        
        # Base score from current emotion
        base_score = (depression_score * 0.7) + (anxiety_score * 0.3)
        
        # Adjust with context
        total_risk_score = base_score + (contextual_risk_factors * 0.2)
        
        if total_risk_score > 0.8:
            return "High", total_risk_score
        elif total_risk_score > 0.4:
            return "Medium", total_risk_score
        else:
            return "Low", total_risk_score
