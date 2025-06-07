import os
import json

def categorize_fixed_cognitive_score(score):
    """
    Categorizes a cognitive score using fixed mean and std (based on your dataset).

    Args:
        score (float): Individual cognitive score.

    Returns:
        str: "high_cognitive", "moderate_cognitive", or "routine"
    """
    fixed_mean = 101.26
    fixed_std = 0.23
    z = (score - fixed_mean) / fixed_std
    if z > 1.0:
        return "high_cognitive"
    elif z < -1.0:
        return "routine"
    else:
        return "moderate_cognitive"
    
file_path = os.path.join(os.path.dirname(__file__), "jobs.json")

def predict_jobs(mbti_type: str, cog_score: float):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {"error": "jobs.json file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in jobs.json"}

    mbti_type = mbti_type.upper()
    if mbti_type not in data:
        return {"error": f"Personality type '{mbti_type}' not found in the dataset"}

    category = categorize_fixed_cognitive_score(cog_score)
    
    recommended_jobs = data[mbti_type].get(category, [])
    good_qualities = data[mbti_type].get("good_qualities", [])
    needs_improvement = data[mbti_type].get("needs_improvement", [])
    return {
        "mbti_type": mbti_type,
        "cog_score": cog_score,
        "cognitive_category": category,
        "recommended_jobs": recommended_jobs,
        "good_qualities": good_qualities,
        "needs_improvement": needs_improvement
        }