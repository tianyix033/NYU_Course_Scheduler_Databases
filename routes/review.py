

































































































from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from datetime import datetime
from database import call_function, call_procedure, execute_query, execute_query_single
from auth_utils import login_required
from psycopg2 import errors as pg_errors

review_bp = Blueprint('review', __name__, url_prefix='/review')


@review_bp.route("/<string:course_id>/<int:instructor_id>", methods=["GET"])
@login_required
def get_reviews(course_id: str, instructor_id: int):
    """
    Display reviews for a specific course-instructor pair.
    """
    try:
        # Get individual reviews using SearchReview function
        reviews = call_function("SearchReview", (course_id, instructor_id))
        
        # Extract course/instructor details from first review (if available)
        course_title = None
        instructor_name = None
        course_description = None
        credits = None
        
        if reviews:
            course_title = reviews[0].get('title')
            instructor_name = reviews[0].get('instructor_name')
            course_description = reviews[0].get('course_description')
            credits = reviews[0].get('credits')
        else:
            # If no reviews, fetch basic course/instructor info
            course_info = execute_query_single(
                "SELECT title, course_description, credits FROM Course WHERE course_id = %s",
                (course_id,)
            )
            if course_info:
                course_title = course_info.get('title')
                course_description = course_info.get('course_description')
                credits = course_info.get('credits')
            
            instructor_info = execute_query_single(
                "SELECT first_name, last_name FROM Instructor WHERE instructor_id = %s",
                (instructor_id,)
            )
            if instructor_info:
                instructor_name = f"{instructor_info.get('first_name')} {instructor_info.get('last_name')}"
        
        # If course or instructor not found
        if not course_title or not instructor_name:
            return render_template('review.html', 
                                 error="Course or Instructor not found",
                                 course_id=course_id,
                                 instructor_id=instructor_id)
        
        # Get average rating from Course_Instructor table
        stats = execute_query_single(
            "SELECT review_sum, review_count FROM Course_Instructor WHERE course_id = %s AND instructor_id = %s",
            (course_id, instructor_id)
        )
        
        review_sum = stats.get('review_sum', 0) if stats else 0
        review_count = stats.get('review_count', 0) if stats else 0
        average_rating = round(review_sum / review_count, 2) if review_count > 0 else 0.0
        
        # Get rating distribution (count of each rating 1-5)
        distribution_results = execute_query(
            "SELECT rating, COUNT(*) as count FROM Review WHERE course_id = %s AND instructor_id = %s GROUP BY rating",
            (course_id, instructor_id),
            fetch=True
        )
        
        # Initialize all ratings with 0
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for row in distribution_results:
            rating_distribution[str(row['rating'])] = row['count']
        
        # Format individual reviews (only include reviews with comments)
        individual_reviews = []
        for r in reviews:
            # Only include reviews that have a comment
            comment = r.get('comment')
            if not comment or comment.strip() == '':
                continue
            
            created_at = r.get('created_at')
            created_at_str = None
            if created_at:
                if hasattr(created_at, 'strftime'):
                    created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
                else:
                    created_at_str = str(created_at)
            
            individual_reviews.append({
                'rating': r.get('rating'),
                'comment': comment,
                'created_at': created_at_str
            })
        
        # Check if current user already has a review for this course-instructor pair
        user_id = session.get('user_id')
        user_has_review = False
        if user_id:
            existing_review = execute_query_single(
                "SELECT rating, comment FROM Review WHERE user_id = %s AND course_id = %s AND instructor_id = %s",
                (user_id, course_id, instructor_id)
            )
            user_has_review = existing_review is not None
        
        return render_template('review.html',
                             course_id=course_id,
                             course_title=course_title,
                             course_description=course_description,
                             credits=credits,
                             instructor_name=instructor_name,
                             instructor_id=instructor_id,
                             average_rating=average_rating,
                             review_count=review_count,
                             rating_distribution=rating_distribution,
                             individual_reviews=individual_reviews,
                             user_has_review=user_has_review)
    
    except Exception as e:
        return render_template('review.html',
                             error=f"Error loading reviews: {str(e)}",
                             course_id=course_id,
                             instructor_id=instructor_id)


@review_bp.route("/<string:course_id>/<int:instructor_id>/create", methods=["POST"])
@login_required
def create_review(course_id: str, instructor_id: int):
    """
    Create a new review for a course-instructor pair.
    """
    user_id = session.get('user_id')
    
    # Validate required fields
    rating = request.form.get('rating')
    comment = request.form.get('comment', '')
    
    if not rating:
        flash('Rating is required.', 'error')
        return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
    
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            flash('Rating must be between 1 and 5.', 'error')
            return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
    except ValueError:
        flash('Invalid rating value.', 'error')
        return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
    
    try:
        # Check if user already has a review for this course-instructor pair
        existing_review = execute_query_single(
            "SELECT user_id FROM Review WHERE user_id = %s AND course_id = %s AND instructor_id = %s",
            (user_id, course_id, instructor_id)
        )
        
        if existing_review:
            flash('You have already submitted a review for this course-instructor pair.', 'error')
            return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
        
        # Call PostReview procedure with current timestamp
        current_timestamp = datetime.now()
        call_procedure("PostReview", (user_id, course_id, instructor_id, rating, comment, current_timestamp), fetch=False)
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
    
    except pg_errors.UniqueViolation:
        # Handle duplicate review (shouldn't happen since we check first, but just in case)
        flash('You have already submitted a review for this course-instructor pair.', 'error')
        return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))
    except Exception as e:
        flash(f'Error submitting review: {str(e)}', 'error')
        return redirect(url_for('review.get_reviews', course_id=course_id, instructor_id=instructor_id))

