# ========== ATTENDANCE ==========
@app.route('/take_attendance/<int:subject_id>')
def take_attendance(subject_id):
    flash("Take Attendance feature coming soon!", "info")
    return redirect(url_for('teacher_dashboard'))

@app.route('/view_attendance/<int:subject_id>')
def view_attendance(subject_id):
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
    
    try:
        conn = get_db_connection()
        subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (subject_id, session['teacher_id'])).fetchone()
        
        if not subject:
            flash("Subject not found", "error")
            return redirect(url_for('teacher_dashboard'))
        
        attendance_records = conn.execute("""SELECT s.roll_no, s.name, a.date, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.subject_id = ?
            ORDER BY a.date DESC, s.roll_no""", (subject_id,)).fetchall()
        
        conn.close()
        return render_template('view_attendance.html', subject=subject, attendance_records=attendance_records)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))