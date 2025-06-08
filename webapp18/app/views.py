from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from . import db
from datetime import datetime, date, timedelta
from app.models import Cashflow, Budget, SavingGoal, Category, User, IncomeCategory
from app.modules.cashflow import net_cash_flow, summarise_month, Transaction, TransactionKind, Category as CashflowCategory, category_breakdown
from sqlalchemy import func
from calendar import monthrange
from collections import OrderedDict
from werkzeug.security import generate_password_hash
import random
import statistics

views = Blueprint('views', __name__)

def get_previous_month(date, n):
    """Get the date n months before the given date."""
    year = date.year
    month = date.month - n
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)

def create_sample_data(user_id):
    # Create sample cashflows
    current_date = datetime.now().date()
    sample_cashflows = [
        # Income
        Cashflow(user_id=user_id, amount=15000000, kind='Income', category='Full‑time Income', date=current_date),
        Cashflow(user_id=user_id, amount=2000000, kind='Income', category='Freelance Income', date=current_date - timedelta(days=5)),
        
        # Expenses
        Cashflow(user_id=user_id, amount=5000000, kind='Expense', category='Essential Spending', date=current_date - timedelta(days=2)),
        Cashflow(user_id=user_id, amount=2000000, kind='Expense', category='Shopping & Entertainment', date=current_date - timedelta(days=3)),
        Cashflow(user_id=user_id, amount=1000000, kind='Expense', category='Health', date=current_date - timedelta(days=4)),
        Cashflow(user_id=user_id, amount=3000000, kind='Expense', category='Education', date=current_date - timedelta(days=6)),
        
        # Savings
        Cashflow(user_id=user_id, amount=2000000, kind='Savings', category='Emergency Fund', date=current_date - timedelta(days=1)),
    ]

    print("hello world")
    
    # Create sample budgets for current month
    current_month = current_date.strftime('%Y-%m')
    sample_budgets = [
        Budget(user_id=user_id, category='Essential Spending', month=current_month, planned_amount=6000000),
        Budget(user_id=user_id, category='Shopping & Entertainment', month=current_month, planned_amount=3000000),
        Budget(user_id=user_id, category='Health', month=current_month, planned_amount=2000000),
        Budget(user_id=user_id, category='Education', month=current_month, planned_amount=4000000),
    ]
    
    # Create sample saving goals
    sample_goals = [
        SavingGoal(
            user_id=user_id,
            name='Emergency Fund',
            total_amount=50000000,
            start_date=current_date - timedelta(days=30),
            target_date=current_date + timedelta(days=180),
            past_savings=10000000
        ),
        SavingGoal(
            user_id=user_id,
            name='Vacation Fund',
            total_amount=30000000,
            start_date=current_date - timedelta(days=15),
            target_date=current_date + timedelta(days=90),
            past_savings=5000000
        )
    ]
    
    try:
        # Add all sample data
        db.session.add_all(sample_cashflows)
        db.session.add_all(sample_budgets)
        db.session.add_all(sample_goals)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {str(e)}")
        return False

@views.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return render_template('landing_page.html')

@views.route('/about-us')
def about_us():
    return render_template('about_us.html')

@views.route('/dashboard')
@login_required
def dashboard():
    # Get all cashflows for the current user
    user_cashflows = Cashflow.query.filter_by(user_id=current_user.id).all()
    
    # Get the last 6 months in chronological order
    current_date = datetime.now()
    current_month = current_date.strftime('%Y-%m')
    months_data = []
    for i in range(5, -1, -1):
        month_date = get_previous_month(current_date, i)
        month_label = month_date.strftime('%b %Y')
        month_key = month_date.strftime('%Y-%m')
        
        # Calculate totals for this month
        month_income = int(sum(txn.amount for txn in user_cashflows 
                         if txn.kind == 'Income' and txn.date.strftime('%Y-%m') == month_key))
        month_expense = int(sum(txn.amount for txn in user_cashflows 
                          if txn.kind == 'Expense' and txn.date.strftime('%Y-%m') == month_key
                          and txn.payment_method not in ['Account Payable', 'Account Receivable']))
        month_savings = int(sum(txn.amount for txn in user_cashflows 
                          if txn.kind == 'Savings' and txn.date.strftime('%Y-%m') == month_key))
        month_balance = month_income - month_expense - month_savings
        
        # Calculate expense categories for this month
        month_expense_categories = {}
        for txn in user_cashflows:
            if (txn.kind == 'Expense' and txn.category and 
                txn.date.strftime('%Y-%m') == month_key and
                txn.payment_method not in ['Account Payable', 'Account Receivable']):
                if txn.category not in month_expense_categories:
                    month_expense_categories[txn.category] = 0
                month_expense_categories[txn.category] += int(txn.amount)
        
        months_data.append({
            'label': month_label,
            'date': month_date,
            'income': month_income,
            'expense': month_expense,
            'savings': month_savings,
            'balance': month_balance,
            'expense_categories': month_expense_categories
        })
    
    # Get current month's data
    current_month_data = next((m for m in months_data if m['date'].strftime('%Y-%m') == current_month), None)
    
    if current_month_data:
        formatted_income = "{:,}".format(current_month_data['income'])
        formatted_expense = "{:,}".format(current_month_data['expense'])
        formatted_savings = "{:,}".format(current_month_data['savings'])
        formatted_balance = "{:,}".format(current_month_data['balance'])
        is_positive = current_month_data['balance'] >= 0
        current_expense_categories = current_month_data['expense_categories']
    else:
        formatted_income = "0"
        formatted_expense = "0"
        formatted_savings = "0"
        formatted_balance = "0"
        is_positive = True
        current_expense_categories = {}
    
    # Create monthly data for charts
    monthly_data = {
        'labels': [m['label'] for m in months_data],
        'income': [m['income'] for m in months_data],
        'expense': [m['expense'] for m in months_data],
        'savings': [m['savings'] for m in months_data],
        'balance': [m['balance'] for m in months_data],
        'expense_categories': [m['expense_categories'] for m in months_data]
    }
    
    return render_template(
        "dashboard.html", 
        user=current_user, 
        total_income=formatted_income, 
        total_expense=formatted_expense,
        total_savings=formatted_savings,
        net_balance=formatted_balance,
        is_positive=is_positive,
        expense_categories=current_expense_categories,
        monthly_data=monthly_data
    )

@views.route('/add-cashflow', methods=['POST'])
@login_required
def add_cashflow():
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form['amount'].replace(',', ''))
            kind = request.form['kind']
            category = request.form.get('category')
            payment_method = request.form.get('payment_method') if kind == 'Expense' else None
            account_name = request.form.get('account_name') if payment_method in ['Account Payable', 'Account Receivable'] else None
            date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()

            # Validate category based on transaction kind (no longer strictly validating against enums for flexibility)
            # The frontend now ensures the correct category name (either from dropdown or custom input)
            # is sent in the 'category' field.
            
            # For Savings, ensure a valid saving goal or new custom category is handled.
            if kind == 'Savings':
                # Get all saving goals for the user
                valid_saving_goal_names = [goal.name for goal in current_user.saving_goals]
                if not valid_saving_goal_names and category != 'Other': # If no goals and not 'Other', prompt to create goal
                    flash('Please create a saving goal first', 'error')
                    return redirect(url_for('views.cashflows'))
                
                # If 'Other' is selected, and it's a new custom category, allow it.
                # Otherwise, it must be an existing saving goal.
                if category != 'Other' and category not in valid_saving_goal_names:
                    flash('Invalid category for Savings transaction', 'error')
                    return redirect(url_for('views.cashflows'))

            # Create new cashflow
            new_cashflow = Cashflow(
                user_id=current_user.id,
                amount=amount,
                kind=kind,
                category=category,
                payment_method=payment_method,
                account_name=account_name,
                date=date
            )

            # Add to database
            db.session.add(new_cashflow)
            db.session.commit()
            flash("Cashflow entry saved successfully!", category="success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving entry: {str(e)}", category="error")
        
        return redirect(url_for('views.cashflows'))

@views.route('/cashflows')
@login_required
def cashflows():
    # Get the selected month from query parameters, default to 'all' for all transactions
    selected_month = request.args.get('month', 'all')
    
    # Query all cashflows for the user
    user_cashflows = Cashflow.query.filter_by(user_id=current_user.id)
    
    # Filter by selected month only if a specific month is selected
    if selected_month != 'all':
        user_cashflows = user_cashflows.filter(
            func.strftime('%Y-%m', Cashflow.date) == selected_month
        )
    
    # Get all months that have cashflows for the dropdown
    months_query = db.session.query(
        func.strftime('%Y-%m', Cashflow.date).label('month')
    ).filter_by(user_id=current_user.id).distinct().order_by('month').all()
    
    # Create month options list with 'All Transactions' as first option
    month_options = ['all'] + [m[0] for m in months_query]
    
    # Get the filtered cashflows ordered by date
    user_cashflows = user_cashflows.order_by(Cashflow.date.desc()).all()
    
    return render_template(
        "cashflows.html",
        user=current_user,
        cashflows=user_cashflows,
        month_options=month_options,
        month=selected_month,
        datetime=datetime,
        categories=[c.value for c in Category]
    )

@views.route('/delete-cashflow', methods=['POST'])
@login_required
def delete_cashflow():
    try:
        cashflow_id = request.json['cashflowId']
        cashflow = Cashflow.query.get(cashflow_id)
        if cashflow and cashflow.user_id == current_user.id:
            db.session.delete(cashflow)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Cashflow not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    if request.method == 'POST':
        try:
            # Handle budget updates
            category = request.form.get('category')
            month = request.form.get('month')
            planned_amount = float(request.form.get('planned_amount').replace(',', ''))
            
            # Validate that category is a valid Category enum value
            if category not in [c.value for c in Category]:
                flash('Invalid category selected', 'error')
                return redirect(url_for('views.budget'))
            
            # Check if budget already exists for this category and month
            budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=category,
                month=month
            ).first()
            
            if budget:
                budget.planned_amount = planned_amount
            else:
                budget = Budget(
                    user_id=current_user.id,
                    category=category,
                    month=month,
                    planned_amount=planned_amount
                )
                db.session.add(budget)
            
            db.session.commit()
            flash('Budget updated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error updating budget: {str(e)}', 'error')
    
    # Get current month's budgets and spending
    current_month = datetime.now().strftime('%Y-%m')
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month
    ).all()
    
    # Get all cashflows for the current month
    cashflows = Cashflow.query.filter(
        Cashflow.user_id == current_user.id,
        Cashflow.kind == 'Expense',
        func.strftime('%Y-%m', Cashflow.date) == current_month,
        ~Cashflow.payment_method.in_(['Account Payable', 'Account Receivable'])
    ).all()
    
    # Create a dictionary to store category totals
    category_totals = {category.value: 0 for category in Category}
    for cashflow in cashflows:
        if cashflow.category in category_totals:
            category_totals[cashflow.category] = category_totals[cashflow.category] + float(cashflow.amount)
    
    # Calculate total actual spending from cashflows
    total_actual = sum(float(cf.amount) for cf in cashflows)
    
    # Calculate actual spending for each category
    budget_data = []
    total_planned = 0
    alerts = []
    
    # Ensure we have budgets for all categories
    existing_budget_categories = {b.category for b in budgets}
    for category in Category:
        if category.value not in existing_budget_categories and category != Category.OTHER:
            budget_data.append({
                'category': category.value,
                'planned': 0,
                'actual': category_totals[category.value],
                'remaining': -category_totals[category.value],
                'usage_percent': 100 if category_totals[category.value] > 0 else 0
            })
    
    for budget in budgets:
        actual_spending = category_totals.get(budget.category, 0)
        usage_percent = budget.calculate_usage(actual_spending)
        remaining = budget.get_remaining(actual_spending)
        
        # Generate alerts based on usage
        if usage_percent > 100:
            alerts.append({
                'type': 'danger',
                'message': f'❌ You have exceeded your budget for {budget.category}!'
            })
        elif usage_percent > 90:
            alerts.append({
                'type': 'warning',
                'message': f'⚠ You\'re at {usage_percent:.1f}% of your budget for {budget.category}.'
            })
        
        budget_data.append({
            'category': budget.category,
            'planned': budget.planned_amount,
            'actual': actual_spending,
            'remaining': remaining,
            'usage_percent': usage_percent
        })
        
        total_planned += budget.planned_amount
    
    # Sort budget data by category name
    budget_data.sort(key=lambda x: x['category'])

    # Check if total budget is exceeded
    if len([d for d in budget_data if d['usage_percent'] > 100]) >= 3:
        alerts.append({
            'type': 'danger',
            'message': 'Spending is drifting from plan in multiple areas.'
        })

    return render_template(
        'budget.html',
        user=current_user,
        budget_data=budget_data,
        alerts=alerts,
        total_planned=total_planned,
        total_actual=total_actual,
        current_month=current_month,
        categories=[c.value for c in Category if c != Category.OTHER],  # Pass categories to template
        min=min
    )

@views.route('/saving-goals')
@login_required
def saving_goals_page():
    # Get saving goals
    user_saving_goals = SavingGoal.query.filter_by(user_id=current_user.id).all()
    goals_data = []

    for goal in user_saving_goals:
        # Calculate current savings from cashflows
        savings_cashflows = Cashflow.query.filter(
            Cashflow.user_id == current_user.id,
            Cashflow.kind == 'Savings',
            Cashflow.category == goal.name,  # Only count savings for this specific goal
            Cashflow.date >= goal.start_date,
            Cashflow.date <= goal.target_date
        ).all()

        current_savings = sum(float(cf.amount) for cf in savings_cashflows)

        # Calculate monthly saving (if goal started in current month)
        if goal.start_date.year == datetime.now().year and goal.start_date.month == datetime.now().month:
            current_monthly_saving = current_savings
        else:
            months_active = ((datetime.now().year - goal.start_date.year) * 12 +
                           datetime.now().month - goal.start_date.month)
            current_monthly_saving = current_savings / max(1, months_active)

        progress = goal.calculate_progress(current_savings)

        goals_data.append({
            'id': goal.id,
            'name': goal.name,
            'total_amount': goal.total_amount,
            'current_savings': current_savings,
            'monthly_required': goal.calculate_monthly_saving(),
            'current_monthly_saving': current_monthly_saving,
            'progress': progress,
            'on_track': goal.is_on_track(current_monthly_saving),
            'start_date': goal.start_date,
            'target_date': goal.target_date,
            'saving_gap': goal.get_saving_gap(current_monthly_saving)
        })

    # Get saving goal alerts (if any)
    alerts = []
    # You might want to add specific saving goal related alerts here if needed

    return render_template(
        'saving_goals.html',
        user=current_user,
        goals_data=goals_data,
        alerts=alerts,  # Pass alerts to the template
        datetime=datetime
    )

@views.route('/add-saving-goal', methods=['POST'])
@login_required
def add_saving_goal():
    try:
        name = request.form.get('name')
        total_amount = float(request.form.get('total_amount').replace(',', ''))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        target_date = datetime.strptime(request.form.get('target_date'), '%Y-%m-%d').date()
        
        # Make past_savings optional with default 0
        past_savings_str = request.form.get('past_savings', '').strip()
        past_savings = float(past_savings_str.replace(',', '')) if past_savings_str else 0
        
        goal = SavingGoal(
            user_id=current_user.id,
            name=name,
            total_amount=total_amount,
            start_date=start_date,
            target_date=target_date,
            past_savings=past_savings
        )
        
        db.session.add(goal)
        db.session.commit()
        
        flash('Saving goal added successfully!', 'success')
        # Redirect to the saving goals page
        return redirect(url_for('views.saving_goals_page'))
        
    except Exception as e:
        flash(f'Error adding saving goal: {str(e)}', 'error')
        # Redirect to the saving goals page on error
        return redirect(url_for('views.saving_goals_page'))

@views.route('/delete-saving-goal', methods=['POST'])
@login_required
def delete_saving_goal():
    try:
        goal_id = request.json['goalId']
        goal = SavingGoal.query.get(goal_id)
        if goal and goal.user_id == current_user.id:
            db.session.delete(goal)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Goal not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/edit-saving-goal', methods=['POST'])
@login_required
def edit_saving_goal():
    try:
        goal_id = request.form.get('goal_id')
        name = request.form.get('name')
        total_amount = float(request.form.get('total_amount').replace(',', ''))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        target_date = datetime.strptime(request.form.get('target_date'), '%Y-%m-%d').date()
        
        # Get the goal and verify ownership
        goal = SavingGoal.query.get(goal_id)
        if not goal or goal.user_id != current_user.id:
            return jsonify({"success": False, "error": "Goal not found or unauthorized"}), 404
        
        # If the name has changed, update all related cashflows
        if goal.name != name:
            # Update all cashflows that reference this goal
            # Need to import Cashflow and db from app.models and . respectively
            from app.models import Cashflow
            db.session.query(Cashflow).filter(
                Cashflow.user_id==current_user.id,
                Cashflow.kind=='Savings',
                Cashflow.category==goal.name
            ).update({'category': name})
        
        # Update goal details
        goal.name = name
        goal.total_amount = total_amount
        goal.start_date = start_date
        goal.target_date = target_date
        
        db.session.commit()
        flash('Saving goal updated successfully!', 'success')
        # Redirect to the saving goals page
        return redirect(url_for('views.saving_goals_page'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating saving goal: {str(e)}', 'error')
        # Redirect to the saving goals page on error
        return redirect(url_for('views.saving_goals_page'))

@views.route('/create-test-account')
def create_test_account():
    # Check if test account already exists
    test_user = User.query.filter_by(email='test@gmail.com').first()
    if test_user:
        return 'Test account already exists!'
    
    # Create new test account
    new_user = User(
        email='test@gmail.com',
        first_name='VaRiors',
        password=generate_password_hash('testpassword', method='pbkdf2:sha256')
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Create sample data for the new user
        if create_sample_data(new_user.id):
            return 'Test account and sample data created successfully!'
        else:
            return 'Test account created but failed to create sample data.'
            
    except Exception as e:
        db.session.rollback()
        return f'Error creating test account: {str(e)}'

@views.route('/outstanding')
@login_required
def outstanding():
    # Get all cashflows for the current user that are Account Payable or Account Receivable
    user_cashflows = Cashflow.query.filter(
        Cashflow.user_id == current_user.id,
        Cashflow.payment_method.in_(['Account Payable', 'Account Receivable'])
    ).order_by(Cashflow.date.desc()).all()
    
    # Separate into payable and receivable
    payables = [cf for cf in user_cashflows if cf.payment_method == 'Account Payable']
    receivables = [cf for cf in user_cashflows if cf.payment_method == 'Account Receivable']
    
    # Calculate totals
    total_payable = sum(float(cf.amount) for cf in payables)
    total_receivable = sum(float(cf.amount) for cf in receivables)
    
    # Get all categories for the dropdown
    categories = [c.value for c in Category]
    
    return render_template(
        "outstanding.html",
        user=current_user,
        payables=payables,
        receivables=receivables,
        total_payable=total_payable,
        total_receivable=total_receivable,
        categories=categories,
        datetime=datetime
    )

@views.route('/edit-cashflow', methods=['POST'])
@login_required
def edit_cashflow():
    if request.method == 'POST':
        try:
            cashflow_id = request.form.get('cashflow_id')
            amount = float(request.form['amount'].replace(',', ''))
            date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
            category = request.form.get('category')
            account_name = request.form.get('account_name')
            payment_method = request.form.get('payment_method')

            # Get the cashflow and verify ownership
            cashflow = Cashflow.query.get(cashflow_id)
            if not cashflow or cashflow.user_id != current_user.id:
                flash('Transaction not found or unauthorized', 'error')
                return redirect(url_for('views.outstanding'))

            # Update the cashflow
            cashflow.amount = amount
            cashflow.date = date
            cashflow.category = category
            cashflow.account_name = account_name
            cashflow.payment_method = payment_method

            db.session.commit()
            flash('Transaction updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating transaction: {str(e)}', 'error')
        
        return redirect(url_for('views.cashflows'))

@views.route('/emergency-fund')
@login_required
def emergency_fund():
    # Get all cashflows for the current user
    user_cashflows = Cashflow.query.filter_by(user_id=current_user.id).all()

    # Convert cashflows to transactions for the cashflow module
    from app.modules.cashflow import Transaction, TransactionKind, Category
    from app.models import IncomeCategory
    
    def safe_category(value):
        try:
            return Category(value)
        except ValueError:
            return Category.OTHER
            
    def safe_income_category(value):
        try:
            return IncomeCategory(value)
        except ValueError:
            return IncomeCategory.FULL_TIME  # Default to full-time income if category is invalid
    
    transactions = []
    for cf in user_cashflows:
        try:
            transaction = Transaction(
                amount=float(cf.amount),
                kind=TransactionKind.EXPENSE if cf.kind == 'Expense' else TransactionKind.INCOME,
                category=safe_category(cf.category) if cf.category else Category.OTHER,
                income_category=safe_income_category(cf.category) if cf.kind == 'Income' else None,
                txn_date=cf.date
            )
            transactions.append(transaction)
        except Exception as e:
            print(f"Error converting cashflow to transaction: {e}")
            continue

    # Get monthly summaries
    from app.modules.cashflow import monthly_series
    monthly_summaries = monthly_series(transactions)

    # Calculate average monthly expenses and standard deviation
    monthly_expenses = [summary.expense for summary in monthly_summaries]

    avg_monthly_expenses = statistics.mean(monthly_expenses) if monthly_expenses else 0
    std_dev_expenses = statistics.stdev(monthly_expenses) if len(monthly_expenses) > 1 else 0

    # Calculate monthly expenses by category for each month
    categorized_monthly_expenses = {}
    for cf in user_cashflows:
        if cf.kind == 'Expense' and cf.payment_method not in ['Account Payable', 'Account Receivable']:
            month_key = cf.date.strftime('%Y-%m')
            category = cf.category if cf.category else Category.OTHER.value
            amount = float(cf.amount)

            if month_key not in categorized_monthly_expenses:
                categorized_monthly_expenses[month_key] = {}
            if category not in categorized_monthly_expenses[month_key]:
                categorized_monthly_expenses[month_key][category] = 0
            categorized_monthly_expenses[month_key][category] += amount

    return render_template(
        'emergency_fund.html',
        user=current_user,
        avg_monthly_expenses=avg_monthly_expenses,
        std_dev_expenses=std_dev_expenses,
        categorized_monthly_expenses=categorized_monthly_expenses
    )

@views.route('/calculate-customized-emergency-fund', methods=['POST'])
@login_required
def calculate_customized_emergency_fund():
    try:
        data = request.get_json()
        scenarios = data.get('scenarios', [])
        # Formula: ∑[expense covered by you × frequency] for valid scenarios
        total_customized_expense = 0
        formula_breakdown = []
        for scenario in scenarios:
            expense_covered = float(scenario.get('expense_covered', 0))
            frequency = float(scenario.get('frequency', 1))
            if frequency > 0 and expense_covered > 0:
                scenario_total = expense_covered * frequency
                total_customized_expense += scenario_total
                formula_breakdown.append({
                    'expense_covered': expense_covered,
                    'frequency': frequency,
                    'subtotal': scenario_total
                })
        return jsonify({
            'success': True,
            'total_expense_per_period': total_customized_expense,
            'customized_emergency_fund': total_customized_expense,
            'formula_breakdown': formula_breakdown
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@views.route('/calculate-months-to-target', methods=['POST'])
@login_required
def calculate_months_to_target():
    try:
        data = request.get_json()
        target_amount = float(data.get('target_amount', 0))
        current_savings = float(data.get('current_savings', 0))
        monthly_dedication = float(data.get('monthly_dedication', 0))
        
        # Formula: (target emergency amount - current emergency savings) / monthly dedication amount
        if monthly_dedication <= 0:
            return jsonify({
                'success': False,
                'error': 'Monthly dedication amount must be greater than 0'
            }), 400
        
        months_to_target = (target_amount - current_savings) / monthly_dedication
        
        # Ensure the result is greater than 0 and handle special cases
        if current_savings >= target_amount:
            return jsonify({
                'success': True,
                'months_to_target': 0,
                'message': 'Target already reached!',
                'is_target_reached': True
            })
        elif months_to_target <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid calculation: Please check your inputs'
            }), 400
        else:
            # Round to 2 decimal places
            months_to_target = round(months_to_target, 2)
            
            # Check if it takes too long
            needs_adjustment = months_to_target > 6
            
            return jsonify({
                'success': True,
                'months_to_target': months_to_target,
                'needs_adjustment': needs_adjustment,
                'is_target_reached': False,
                'formula_used': f'({target_amount} - {current_savings}) / {monthly_dedication} = {months_to_target}'
            })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            'success': False,
            'error': 'Invalid input values. Please enter valid numbers.'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@views.route('/calculate-simple-emergency-fund', methods=['POST'])
@login_required
def calculate_simple_emergency_fund():
    try:
        data = request.get_json()
        months = int(data.get('months', 0))
        selected_categories = data.get('categories', [])
        # Get all cashflows for the current user
        user_cashflows = Cashflow.query.filter_by(user_id=current_user.id).all()
        # Calculate monthly expenses by category for each month
        categorized_monthly_expenses = {}
        for cf in user_cashflows:
            if cf.kind == 'Expense' and cf.payment_method not in ['Account Payable', 'Account Receivable']:
                month_key = cf.date.strftime('%Y-%m')
                category = cf.category if cf.category else Category.OTHER.value
                amount = float(cf.amount)
                if month_key not in categorized_monthly_expenses:
                    categorized_monthly_expenses[month_key] = {}
                if category not in categorized_monthly_expenses[month_key]:
                    categorized_monthly_expenses[month_key][category] = 0
                categorized_monthly_expenses[month_key][category] += amount
        # Calculate average monthly expense for selected categories
        total_sum = 0
        months_with_data = 0
        for month_key in categorized_monthly_expenses:
            month_total = 0
            for cat in selected_categories:
                if cat in categorized_monthly_expenses[month_key]:
                    month_total += categorized_monthly_expenses[month_key][cat]
            if month_total > 0:
                total_sum += month_total
                months_with_data += 1
        avg_monthly_expense = total_sum / months_with_data if months_with_data > 0 else 0
        result = avg_monthly_expense * months
        return jsonify({
            'success': True,
            'months': months,
            'avg_monthly_expense': avg_monthly_expense,
            'result': result,
            'formula': f'{months} × {int(avg_monthly_expense)} = {int(result)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
