from flask import Blueprint, session, redirect, render_template_string, request, jsonify, url_for
from sqlalchemy import func, exists, Integer, Boolean
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from ..db import SessionLocal
from ..models import Question, QuestionVote, QuestionStepikModule, StepikModule, TelegramUser, QuestionAnswer, TelegramTopic, User
from ..telegram_auth import validate_webapp_init_data
from ..config import Config
import requests

questions_bp = Blueprint("questions", __name__, url_prefix="/questions")


# ============================================================================
# HTML TEMPLATE
# ============================================================================

QUESTIONS_PAGE_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📚 Вопросы курса</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f5f5f5;
      color: #333;
      line-height: 1.6;
      padding-bottom: 40px;
    }
    
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .header h1 {
      font-size: 24px;
      margin-bottom: 10px;
    }
    
    .header .subtitle {
      opacity: 0.9;
      font-size: 14px;
    }
    
    .container {
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
    }
    
    /* Фильтры */
    .filters {
      background: white;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .filter-row {
      margin-bottom: 15px;
    }
    
    .filter-row:last-child {
      margin-bottom: 0;
    }
    
    .filter-label {
      font-weight: 600;
      font-size: 13px;
      color: #666;
      margin-bottom: 8px;
      display: block;
    }
    
    .filter-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    .filter-btn {
      padding: 6px 12px;
      border: 1px solid #e0e0e0;
      background: white;
      border-radius: 16px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
      text-decoration: none;
      color: #333;
      display: inline-block;
    }
    
    .filter-btn:hover {
      border-color: #667eea;
      color: #667eea;
    }
    
    .filter-btn.active {
      background: #667eea;
      color: white;
      border-color: #667eea;
    }
    
    /* Карточки вопросов */
    .questions-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .question-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .question-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    
    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
      gap: 12px;
    }
    
    .question-header-left {
      flex: 1;
      min-width: 0;
    }
    
    .question-header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    
    .question-modules {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 8px;
    }
    
    .module-badge {
      background: #e3f2fd;
      color: #1976d2;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      text-decoration: none;
      display: inline-block;
    }
    
    .module-badge:hover {
      background: #1976d2;
      color: white;
      transform: translateY(-1px);
    }
    
    .status-badge {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
      text-decoration: none;
      display: inline-block;
    }
    
    .status-badge:hover {
      transform: translateY(-1px);
      opacity: 0.8;
    }
    
    .status-voting { background: #fff3e0; color: #f57c00; }
    .status-scheduled { background: #e1f5fe; color: #0288d1; }
    .status-posted { background: #e8f5e9; color: #388e3c; }
    .status-closed { background: #f3e5f5; color: #7b1fa2; }
    .status-archived { background: #ede7f6; color: #512da8; }
    
    .question-title {
      font-size: 18px;
      font-weight: 600;
      color: #222;
      margin-bottom: 8px;
    }
    
    .question-body {
      color: #555;
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 12px;
    }
    
    .vote-button {
      display: flex;
      align-items: center;
      gap: 6px;
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
      padding: 6px 12px;
      border-radius: 20px;
      transition: all 0.2s;
    }
    
    .vote-button:hover {
      background: #f5f5f5;
    }
    
    .vote-button.voted {
      color: #e91e63;
    }
    
    .vote-button.voted .heart {
      animation: heartbeat 0.3s;
    }
    
    @keyframes heartbeat {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.2); }
    }
    
    .summary-block {
      background: #f9fbe7;
      border-left: 4px solid #9ccc65;
      padding: 12px;
      margin-top: 12px;
      border-radius: 4px;
    }
    
    .summary-block strong {
      color: #558b2f;
      display: block;
      margin-bottom: 6px;
    }
    
    .read-more-btn {
      display: inline-block;
      margin-top: 8px;
      color: #558b2f;
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
    }
    
    .read-more-btn:hover {
      text-decoration: underline;
    }
    
    .telegram-link {
      display: inline-block;
      margin-top: 8px;
      padding: 6px 12px;
      background: #0088cc;
      color: white;
      text-decoration: none;
      border-radius: 6px;
      font-size: 13px;
    }
    
    .telegram-link:hover {
      background: #006699;
    }
    
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #999;
    }
    
    .empty-state-icon {
      font-size: 64px;
      margin-bottom: 16px;
    }
    
    .edit-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      background: #667eea;
      color: white;
      text-decoration: none;
      border-radius: 50%;
      font-size: 14px;
      transition: all 0.2s;
      margin-right: 8px;
    }
    
    .edit-btn:hover {
      background: #5568d3;
      transform: scale(1.1);
    }
    
    .add-question-btn {
      display: block;
      width: fit-content;
      margin: 20px auto;
      padding: 12px 30px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      text-decoration: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
      transition: all 0.3s;
    }
    
    .add-question-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    /* Адаптив */
    @media (max-width: 600px) {
      .container { padding: 12px; }
      .header { padding: 16px; }
      .header h1 { font-size: 20px; }
      .question-card { padding: 16px; }
      .filter-buttons { font-size: 13px; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📚 Вопросы курса</h1>
    <div class="subtitle">Голосуйте за интересные вопросы — самые популярные обсуждаются в группе</div>
  </div>
  
  <div class="container">
    <!-- Фильтры -->
    <div class="filters">
      <!-- Строка 1: Темы -->
      <div class="filter-row">
        <div class="filter-label">📌 Тема:</div>
        <div class="filter-buttons">
          <a href="{{ url_for('questions.list_questions', status=current_status, period=current_period) }}" 
             class="filter-btn {% if current_topic == 'all' %}active{% endif %}">Все</a>
          {% for module in modules %}
            <a href="{{ url_for('questions.list_questions', topic=module.id, status=current_status, period=current_period) }}" 
               class="filter-btn {% if current_topic == module.id|string %}active{% endif %}">
              {{ module.title }}
            </a>
          {% endfor %}
        </div>
      </div>
      
      <!-- Строка 2: Статусы -->
      <div class="filter-row">
        <div class="filter-label">🔖 Статус:</div>
        <div class="filter-buttons">
          <a href="{{ url_for('questions.list_questions', topic=current_topic, period=current_period) }}" 
             class="filter-btn {% if current_status == 'all' %}active{% endif %}">Все</a>
          <a href="{{ url_for('questions.list_questions', topic=current_topic, status='VOTING', period=current_period) }}" 
             class="filter-btn {% if current_status == 'VOTING' %}active{% endif %}">В голосовании</a>
          <a href="{{ url_for('questions.list_questions', topic=current_topic, status='POSTED', period=current_period) }}" 
             class="filter-btn {% if current_status == 'POSTED' %}active{% endif %}">В обсуждении</a>
          <a href="{{ url_for('questions.list_questions', topic=current_topic, status='CLOSED', period=current_period) }}" 
             class="filter-btn {% if current_status == 'CLOSED' %}active{% endif %}">Закрыто</a>
          <a href="{{ url_for('questions.list_questions', topic=current_topic, status='ARCHIVED', period=current_period) }}" 
             class="filter-btn {% if current_status == 'ARCHIVED' %}active{% endif %}">Архив</a>
        </div>
      </div>
      
      <!-- Строка 3: Период -->
      <div class="filter-row">
        <div class="filter-label">📅 Период:</div>
        <div class="filter-buttons">
           <a href="{{ url_for('questions.list_questions', topic=current_topic, status=current_status) }}" 
             class="filter-btn {% if current_period == 'all' %}active{% endif %}">Все время</a>
           <a href="{{ url_for('questions.list_questions', topic=current_topic, status=current_status, period='last30') }}" 
             class="filter-btn {% if current_period == 'last30' %}active{% endif %}">Последние 30</a>
           <a href="{{ url_for('questions.list_questions', topic=current_topic, status=current_status, period='week') }}" 
             class="filter-btn {% if current_period == 'week' %}active{% endif %}">За неделю</a>
           <a href="{{ url_for('questions.list_questions', topic=current_topic, status=current_status, period='month') }}" 
             class="filter-btn {% if current_period == 'month' %}active{% endif %}">За месяц</a>
           <a href="{{ url_for('questions.list_questions', topic=current_topic, status=current_status, period='year') }}" 
             class="filter-btn {% if current_period == 'year' %}active{% endif %}">За год</a>
        </div>
      </div>
    </div>
    
    <!-- Список вопросов -->
    <div class="questions-list">
      {% if questions %}
        {% for q in questions %}
          <div class="question-card">
            <div class="question-header">
              <div class="question-header-left">
                <div class="question-modules">
                  {% for module in q.modules %}
                    <a href="{{ url_for('questions.list_questions', topic=module.id, status=current_status, period=current_period) }}" 
                       class="module-badge">{{ module.title }}</a>
                  {% endfor %}
                </div>
              </div>
              <div class="question-header-right">
                {% if user_role and user_role >= 1 %}
                  <a href="{{ url_for('questions.question_detail', question_id=q.id) }}#edit" class="edit-btn">
                    📖
                  </a>
                {% endif %}
                <a href="{{ url_for('questions.list_questions', topic=current_topic, status=q.status, period=current_period) }}" 
                   class="status-badge status-{{ q.status.lower() }}">
                  {{ q.status_label }}
                </a>
                <form method="post" action="{{ url_for('questions.vote', question_id=q.id) }}" class="vote-form" style="margin: 0;">
                  <button type="submit" class="vote-button {% if q.my_vote %}voted{% endif %}" data-question-id="{{ q.id }}">
                    <span class="heart">{% if q.my_vote %}❤️{% else %}🤍{% endif %}</span>
                    <span class="vote-count">{{ q.votes_count }}</span>
                  </button>
                </form>
              </div>
            </div>
            
            {% if q.title %}
              <div class="question-title">{{ q.title }}</div>
            {% endif %}
            
            <div class="question-body">
              {{ q.body_preview }}
            </div>
            
            <!-- Итоговый ответ для архивных вопросов -->
            {% if q.summary %}
              <div class="summary-block">
                <strong>✅ Итог:</strong>
                {{ q.summary }}
                <a href="{{ url_for('questions.question_detail', question_id=q.id) }}" class="read-more-btn">
                  Читать полностью →
                </a>
              </div>
            {% endif %}
            
            <!-- Ссылка на Telegram для обсуждения -->
            {% if q.telegram_link %}
              <a href="{{ q.telegram_link }}" target="_blank" class="telegram-link">
                💬 Перейти к обсуждению в Telegram ({{ q.messages_count - 1 if q.messages_count > 0 else 0 }})
              </a>
            {% endif %}
          </div>
        {% endfor %}
      {% else %}
        <div class="empty-state">
          <div class="empty-state-icon">🤔</div>
          <h3>Вопросов не найдено</h3>
          <p>Попробуйте изменить фильтры или задайте первый вопрос!</p>
        </div>
      {% endif %}
    </div>
    
    {% if user_role and user_role >= 1 %}
      <a href="{{ url_for('questions.question_detail', question_id=0) }}" class="add-question-btn">
        ➕ Добавить вопрос
      </a>
    {% endif %}
  </div>
  
  <script>
    // AJAX для голосования (progressive enhancement)
    document.querySelectorAll('.vote-form').forEach(form => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = form.querySelector('.vote-button');
        const questionId = button.dataset.questionId;
        const heart = button.querySelector('.heart');
        const voteCount = button.querySelector('.vote-count');
        
        try {
          const response = await fetch(`/questions/${questionId}/vote`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            }
          });
          
          if (!response.ok) {
            // Если ошибка авторизации - редирект на login
            if (response.status === 401) {
              window.location.href = '/login';
              return;
            }
            throw new Error('Ошибка голосования');
          }
          
          const data = await response.json();
          
          // Обновляем UI
          button.classList.toggle('voted', data.liked);
          heart.textContent = data.liked ? '❤️' : '🤍';
          voteCount.textContent = data.votes_count;
          
        } catch (error) {
          console.error('Vote error:', error);
          // Fallback на обычную отправку формы
          form.submit();
        }
      });
    });
    
    // Предотвращаем переход по ссылке если она ведёт на текущую страницу
    document.querySelectorAll('.filter-btn, .module-badge, .status-badge').forEach(link => {
      link.addEventListener('click', (e) => {
        const linkUrl = new URL(link.href);
        const currentUrl = new URL(window.location.href);
        
        // Сравниваем pathname и параметры запроса
        if (linkUrl.pathname === currentUrl.pathname && 
            linkUrl.search === currentUrl.search) {
          e.preventDefault();
          return false;
        }
      });
    });
  </script>
</body>
</html>
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_title_with_ai(body: str) -> str:
    """Генерирует краткий заголовок вопроса через OpenAI API."""
    if not Config.OPENAI_API_KEY:
        # Fallback: берем первое предложение
        first_sentence = body.split('.')[0].split('?')[0].strip()
        return first_sentence[:60] if len(first_sentence) > 60 else first_sentence
    
    # Загружаем промпт из файла
    try:
        import os
        # Путь от app/routes/questions.py к корню проекта (на 3 уровня вверх)
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'title_generation.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    except Exception as e:
        print(f"[AI Title] Error loading prompt file: {e}")
        system_prompt = 'Создай краткий заголовок (3-5 слов) для вопроса студента курса по аюрведе и очищению психического тела.'
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {Config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': f'Создай краткий заголовок (максимум 5 слов):\n\n{body[:500]}'
                    }
                ],
                'max_tokens': 30,
                'temperature': 0.7
            },
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            title = data['choices'][0]['message']['content'].strip()
            # Убираем кавычки если есть
            title = title.strip('"\'')
            return title[:60]  # Жесткое ограничение 60 символов
        else:
            print(f"[AI Title] OpenAI API error: {response.text}")
            # Fallback
            first_sentence = body.split('.')[0].split('?')[0].strip()
            return first_sentence[:60]
            
    except Exception as e:
        print(f"[AI Title] Error: {e}")
        # Fallback: берем первое предложение
        first_sentence = body.split('.')[0].split('?')[0].strip()
        return first_sentence[:60] if len(first_sentence) > 60 else first_sentence


def generate_summary_with_ai(answer_text: str) -> str:
    """Генерирует краткое резюме итогового ответа через OpenAI API (1-3 предложения, до 300 символов)."""
    if not Config.OPENAI_API_KEY:
        # Fallback: берем первые 2 предложения
        sentences = answer_text.split('.')[:2]
        summary = '. '.join(s.strip() for s in sentences if s.strip())
        return summary[:300] if len(summary) > 300 else summary
    
    # Загружаем промпт из файла
    try:
        import os
        # Путь от app/routes/questions.py к корню проекта (на 3 уровня вверх)
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'summary_generation.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    except Exception as e:
        print(f"[AI Summary] Error loading prompt file: {e}")
        system_prompt = 'Создай краткое резюме (1-3 предложения) ответа преподавателя курса по аюрведе и очищению психического тела.'
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {Config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': f'Создай краткое резюме (1-3 предложения, до 300 символов) для этого ответа:\n\n{answer_text[:1000]}'
                    }
                ],
                'max_tokens': 100,
                'temperature': 0.7
            },
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            summary = data['choices'][0]['message']['content'].strip()
            # Убираем кавычки если есть
            summary = summary.strip('"\'')
            return summary[:300]  # Жесткое ограничение 300 символов
        else:
            print(f"[AI Summary] OpenAI API error: {response.text}")
            # Fallback
            sentences = answer_text.split('.')[:2]
            summary = '. '.join(s.strip() for s in sentences if s.strip())
            return summary[:300]
            
    except Exception as e:
        print(f"[AI Summary] Error: {e}")
        # Fallback: берем первые 2 предложения
        sentences = answer_text.split('.')[:2]
        summary = '. '.join(s.strip() for s in sentences if s.strip())
        return summary[:300] if len(summary) > 300 else summary


def get_status_label(status: str) -> str:
    """Преобразует статус в человекочитаемую метку."""
    labels = {
        'VOTING': 'В голосовании',
        'SCHEDULED': 'Запланировано',
        'POSTED': 'В обсуждении',
        'CLOSED': 'Закрыто',
        'ARCHIVED': 'Архив'
    }
    return labels.get(status, status)


def get_period_filter(period: str):
    """Возвращает дату для фильтрации по периоду."""
    if period == 'week':
        return datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        return datetime.utcnow() - timedelta(days=30)
    elif period == 'year':
        return datetime.utcnow() - timedelta(days=365)
    return None


# ============================================================================
# ROUTES
# ============================================================================

@questions_bp.route("", methods=["GET"])
def list_questions():
    """Главная страница со списком вопросов и фильтрами."""
    
    # Получаем параметры фильтрации
    topic_filter = request.args.get('topic', 'all')
    status_filter = request.args.get('status', 'all')
    period_filter = request.args.get('period', 'all')
    
    # Получаем текущего пользователя (опционально - для проверки my_vote)
    user_id = session.get("user_id")
    telegram_user_id = None
    
    db = SessionLocal()
    try:
        # Если пользователь авторизован, получаем его telegram_id
        if user_id:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                telegram_user_id = user.telegram_id
        
        # Основной запрос: votes_count теперь поле
        if telegram_user_id:
          my_vote_exists = exists().where(
            QuestionVote.question_id == Question.id,
            QuestionVote.telegram_user_id == telegram_user_id
          )
          query = (
            db.query(
              Question,
              my_vote_exists.label('my_vote')
            )
          )
        else:
          query = (
            db.query(
              Question,
              func.cast(False, Integer).label('my_vote')
            )
          )
        
        # Применяем фильтры
        if topic_filter != 'all':
            query = query.join(
                QuestionStepikModule,
                Question.id == QuestionStepikModule.question_id
            ).filter(QuestionStepikModule.module_id == int(topic_filter))
        
        if status_filter != 'all':
            query = query.filter(Question.status == status_filter)
        
        period_date = get_period_filter(period_filter)
        if period_date:
            query = query.filter(Question.created_at >= period_date)
        # Сортировка: по количеству голосов DESC, затем по дате DESC
        query = query.order_by(
          Question.votes_count.desc(),
          Question.created_at.desc()
        )
        if period_filter == 'last30':
            query = query.limit(30)
        
        results = query.all()

        # Собираем id всех вопросов
        question_ids = [q.id for q, *_ in results]

        # Получаем все модули для всех вопросов одним запросом
        modules_by_qid = {}
        if question_ids:
            qsm = db.query(QuestionStepikModule).filter(QuestionStepikModule.question_id.in_(question_ids)).all()
            module_ids = list({m.module_id for m in qsm})
            modules = db.query(StepikModule).filter(StepikModule.id.in_(module_ids)).all()
            modules_dict = {m.id: m for m in modules}
            for m in qsm:
                modules_by_qid.setdefault(m.question_id, []).append(modules_dict.get(m.module_id))
            # Сортируем модули по позиции
            for qid in modules_by_qid:
                modules_by_qid[qid] = sorted([mod for mod in modules_by_qid[qid] if mod], key=lambda m: m.position)

        # Получаем все ответы одним запросом
        answers = db.query(QuestionAnswer).filter(QuestionAnswer.question_id.in_(question_ids)).all() if question_ids else []
        answers_by_qid = {a.question_id: a for a in answers}

        # Получаем все Telegram темы одним запросом
        topics = db.query(TelegramTopic).filter(TelegramTopic.question_id.in_(question_ids)).all() if question_ids else []
        topics_by_qid = {t.question_id: t for t in topics}

        questions_data = []
        # Определяем количество колонок в results
        if results and len(results[0]) == 3:
            for question, votes_count, my_vote in results:
                modules = modules_by_qid.get(question.id, [])
                answer = answers_by_qid.get(question.id)
                answer_preview = None
                if answer and answer.answer:
                    if len(answer.answer) > 300:
                        answer_preview = answer.answer[:300] + '...'
                    else:
                        answer_preview = answer.answer
                telegram_link = None
                messages_count = 0
                topic = topics_by_qid.get(question.id)
                if topic:
                    telegram_link = f"https://t.me/c/{str(topic.chat_id)[4:]}/{topic.message_thread_id}"
                    messages_count = topic.messages_count or 0
                body_preview = question.body[:300] + '...' if len(question.body) > 300 else question.body
                questions_data.append({
                    'id': question.id,
                    'title': question.title,
                    'body_preview': body_preview,
                    'status': question.status,
                    'status_label': get_status_label(question.status),
                    'votes_count': votes_count,
                    'my_vote': my_vote,
                    'modules': modules,
                    'summary': answer_preview,
                    'telegram_link': telegram_link,
                    'messages_count': messages_count,
                    'created_at': question.created_at
                })
        else:
            for question, my_vote in results:
                modules = modules_by_qid.get(question.id, [])
                answer = answers_by_qid.get(question.id)
                answer_preview = None
                if answer and answer.answer:
                    if len(answer.answer) > 300:
                        answer_preview = answer.answer[:300] + '...'
                    else:
                        answer_preview = answer.answer
                telegram_link = None
                messages_count = 0
                topic = topics_by_qid.get(question.id)
                if topic:
                    telegram_link = f"https://t.me/c/{str(topic.chat_id)[4:]}/{topic.message_thread_id}"
                    messages_count = topic.messages_count or 0
                body_preview = question.body[:300] + '...' if len(question.body) > 300 else question.body
                questions_data.append({
                    'id': question.id,
                    'title': question.title,
                    'body_preview': body_preview,
                    'status': question.status,
                    'status_label': get_status_label(question.status),
                    'votes_count': question.votes_count,
                    'my_vote': my_vote,
                    'modules': modules,
                    'summary': answer_preview,
                    'telegram_link': telegram_link,
                    'messages_count': messages_count,
                    'created_at': question.created_at
                })
        
        # Получаем все модули для фильтров
        all_modules = db.query(StepikModule).order_by(StepikModule.position).all()
        
        # Получаем роль пользователя
        user_role = None
        if user_id:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user_role = user.role
        
        return render_template_string(
            QUESTIONS_PAGE_TEMPLATE,
            questions=questions_data,
            modules=all_modules,
            current_topic=topic_filter,
            current_status=status_filter,
            current_period=period_filter,
            user_id=user_id,
            user_role=user_role
        )
        
    finally:
        db.close()


@questions_bp.route("/<int:question_id>/vote", methods=["POST"])
def vote(question_id: int):
    """Toggle голоса за вопрос. Работает как с AJAX так и с form POST."""
    
    telegram_user_id = None
    
    # Сначала пытаемся получить telegram_user_id из initData (для Mini App)
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    if init_data:
        try:
            import json
            import urllib.parse
            params = dict(item.split('=') for item in init_data.split('&') if '=' in item)
            if 'user' in params:
                user_data = json.loads(urllib.parse.unquote(params['user']))
                telegram_user_id = user_data.get('id')
                print(f"[VOTE] Extracted telegram_user_id from initData: {telegram_user_id}")
        except Exception as e:
            print(f"[VOTE] Error parsing initData: {e}")
    
    # Если не получили из initData, пробуем из сессии
    if not telegram_user_id:
        user_id = session.get("user_id")
        if not user_id:
            # Для AJAX запросов возвращаем 401
            if request.is_json or request.headers.get('Content-Type') == 'application/json' or init_data:
                return jsonify({'error': 'Unauthorized', 'message': 'Требуется авторизация'}), 401
            # Для обычных форм - редирект на login
            return redirect('/login')
        
        db_temp = SessionLocal()
        try:
            user = db_temp.query(User).filter_by(id=user_id).first()
            if user and user.telegram_id:
                telegram_user_id = user.telegram_id
        finally:
            db_temp.close()
    
    if not telegram_user_id:
        if request.is_json or request.headers.get('Content-Type') == 'application/json' or init_data:
            return jsonify({'error': 'No telegram_id', 'message': 'Telegram ID не найден'}), 400
        return redirect('/questions')
    
    db = SessionLocal()
    try:
        # Проверяем существует ли вопрос
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            if request.is_json or request.headers.get('Content-Type') == 'application/json' or init_data:
                return jsonify({'error': 'Not found', 'message': 'Вопрос не найден'}), 404
            return redirect('/questions')
        
        # Проверяем существующий голос
        existing_vote = db.query(QuestionVote).filter_by(
            question_id=question_id,
            telegram_user_id=telegram_user_id
        ).first()
        
        if existing_vote:
            # Снимаем голос
            db.delete(existing_vote)
            liked = False
        else:
            # Ставим голос
            new_vote = QuestionVote(
                question_id=question_id,
                telegram_user_id=telegram_user_id
            )
            db.add(new_vote)
            liked = True
        
        db.commit()
        
        # Получаем votes_count из поля
        votes_count = db.query(Question.votes_count).filter(Question.id == question_id).scalar()
        
        # Для AJAX запросов возвращаем JSON
        if request.is_json or request.headers.get('Content-Type') == 'application/json' or init_data:
            return jsonify({
                'success': True,
                'liked': liked,
                'votes_count': votes_count
            })
        
        # Для обычных форм - редирект обратно
        return redirect(request.referrer or url_for('questions.list_questions'))
        
    except Exception as e:
        db.rollback()
        if request.is_json or request.headers.get('Content-Type') == 'application/json' or init_data:
            return jsonify({'error': 'Server error', 'message': str(e)}), 500
        return redirect('/questions')
    finally:
        db.close()


@questions_bp.route("/<int:question_id>/publish", methods=["POST"])
def publish_question(question_id: int):
    """Публикация вопроса в Telegram форум-группу."""
    
    # Проверяем права (только curator+)
    user_id = session.get("user_id")
    user_role = None
    if user_id:
        db_temp = SessionLocal()
        try:
            user = db_temp.query(User).filter_by(id=user_id).first()
            if user:
                user_role = user.role
        finally:
            db_temp.close()
    
    if not user_role or user_role < 1:
        return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
    
    # Проверяем наличие необходимых параметров
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        return jsonify({'success': False, 'error': 'Telegram не настроен'}), 500
    
    db = SessionLocal()
    try:
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
        
        # Проверяем что вопрос еще не опубликован
        existing_topic = db.query(TelegramTopic).filter_by(question_id=question_id).first()
        if existing_topic:
            return jsonify({'success': False, 'error': 'Вопрос уже опубликован'}), 400
        
        # Формируем название темы (краткий текст)
        topic_name = question.title or question.body[:100]
        if len(topic_name) > 100:
            topic_name = topic_name[:97] + '...'
        
        # Определяем иконку для топика из первого модуля вопроса (если есть)
        icon_custom_emoji_id = None
        if question.modules:
            first_module = question.modules[0]
            if first_module.forum_topic_icon:
                icon_custom_emoji_id = first_module.forum_topic_icon
        
        # Создаем форум топик через Telegram Bot API
        create_topic_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/createForumTopic"
        topic_payload = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'name': topic_name
        }
        
        # Добавляем иконку если она задана
        if icon_custom_emoji_id:
            topic_payload['icon_custom_emoji_id'] = icon_custom_emoji_id
        
        topic_response = requests.post(create_topic_url, json=topic_payload)
        
        if not topic_response.ok:
            return jsonify({
                'success': False, 
                'error': f'Ошибка создания темы: {topic_response.text}'
            }), 500
        
        topic_data = topic_response.json()
        message_thread_id = topic_data['result']['message_thread_id']
        
        # Отправляем сообщение с текстом вопроса в созданную тему
        send_message_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        message_text = question.body  # Заголовок уже в названии темы
        
        message_response = requests.post(send_message_url, json={
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'message_thread_id': message_thread_id,
            'text': message_text,
            'parse_mode': 'Markdown'
        })
        
        if not message_response.ok:
            # Если не удалось отправить сообщение, пробуем закрыть тему
            return jsonify({
                'success': False,
                'error': f'Ошибка отправки сообщения: {message_response.text}'
            }), 500
        
        message_data = message_response.json()
        open_message_id = message_data['result']['message_id']
        
        # Сохраняем связь в базе
        telegram_topic = TelegramTopic(
            question_id=question_id,
            chat_id=int(Config.TELEGRAM_CHAT_ID),
            message_thread_id=message_thread_id,
            open_message_id=open_message_id,
            opened_at=datetime.utcnow(),
            close_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(telegram_topic)
        
        # Обновляем статус вопроса
        question.status = 'POSTED'
        question.posted_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Вопрос опубликован в Telegram',
            'thread_id': message_thread_id
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@questions_bp.route("/<int:question_id>/close-discussion", methods=["POST"])
def close_discussion(question_id):
    """Закрыть обсуждение в Telegram (закрыть тему)."""
    # Проверяем авторизацию и права
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({'success': False, 'error': 'Необходима авторизация'}), 401
    
    db = SessionLocal()
    try:
        # Проверяем права пользователя
        user = db.query(User).filter_by(id=user_id).first()
        if not user or user.role < 1:
            return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
        
        # Получаем вопрос
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
        
        # Проверяем, что вопрос опубликован
        if question.status != 'POSTED':
            return jsonify({'success': False, 'error': 'Вопрос не находится в обсуждении'}), 400
        
        # Получаем данные темы Telegram
        topic = db.query(TelegramTopic).filter_by(question_id=question_id).first()
        if not topic:
            return jsonify({'success': False, 'error': 'Тема в Telegram не найдена'}), 404
        
        # Получаем telegram username текущего пользователя
        telegram_user = None
        if user.telegram_id:
            telegram_user = db.query(TelegramUser).filter_by(id=user.telegram_id).first()
        
        username_text = f"@{telegram_user.username}" if telegram_user and telegram_user.username else "администратором"
        
        # Отправляем сообщение о закрытии в тему
        message_url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage'
        message_response = requests.post(message_url, json={
            'chat_id': topic.chat_id,
            'message_thread_id': topic.message_thread_id,
            'text': f'🔒 Тема закрыта пользователем {username_text}'
        })
        
        # Продолжаем даже если сообщение не отправилось
        if not message_response.ok:
            print(f"[WARNING] Не удалось отправить сообщение о закрытии: {message_response.text}")
        
        # Закрываем тему через Telegram API
        close_url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/closeForumTopic'
        close_response = requests.post(close_url, json={
            'chat_id': topic.chat_id,
            'message_thread_id': topic.message_thread_id
        })
        
        if not close_response.ok:
            error_data = close_response.json()
            return jsonify({
                'success': False,
                'error': f'Ошибка закрытия темы: {error_data.get("description", "Неизвестная ошибка")}'
            }), 500
        
        # Обновляем статус вопроса и время закрытия
        question.status = 'CLOSED'
        topic.closed_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Обсуждение закрыто'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@questions_bp.route("/<int:question_id>/archive", methods=["POST"])
def archive_question(question_id):
    """Архивировать вопрос: открыть тему, опубликовать ответ, закрыть тему."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({'success': False, 'error': 'Необходима авторизация'}), 401
    
    db = SessionLocal()
    try:
        # Проверяем права пользователя
        user = db.query(User).filter_by(id=user_id).first()
        if not user or user.role < 1:
            return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
        
        # Получаем вопрос
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
        
        # Проверяем статус
        if question.status != 'CLOSED':
            return jsonify({'success': False, 'error': 'Можно архивировать только закрытые вопросы'}), 400
        
        # Проверяем наличие ответа
        answer = db.query(QuestionAnswer).filter_by(question_id=question_id).first()
        if not answer or not answer.answer or not answer.answer.strip():
            return jsonify({'success': False, 'error': 'Заполните итоговый ответ перед архивированием'}), 400
        
        # Получаем тему
        topic = db.query(TelegramTopic).filter_by(question_id=question_id).first()
        if not topic:
            return jsonify({'success': False, 'error': 'Тема в Telegram не найдена'}), 404
        
        # 1. Открываем тему
        reopen_url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/reopenForumTopic'
        reopen_response = requests.post(reopen_url, json={
            'chat_id': topic.chat_id,
            'message_thread_id': topic.message_thread_id
        })
        
        if not reopen_response.ok:
            error_data = reopen_response.json()
            return jsonify({
                'success': False,
                'error': f'Ошибка открытия темы: {error_data.get("description", "Неизвестная ошибка")}'
            }), 500
        
        # 2. Отправляем итоговый ответ (максимум 4096 символов в Telegram)
        answer_text = answer.answer
        if len(answer_text) > 4000:
            answer_text = answer_text[:4000] + '...\n\n(ответ обрезан, полный текст см. на сайте)'
        
        final_message = f"✅ **ИТОГОВЫЙ ОТВЕТ**\n\n{answer_text}"
        
        if answer.sources:
            sources_text = answer.sources.text if hasattr(answer.sources, 'text') else str(answer.sources)
            final_message += f"\n\n📚 Источники: {sources_text}"
        
        message_url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage'
        message_response = requests.post(message_url, json={
            'chat_id': topic.chat_id,
            'message_thread_id': topic.message_thread_id,
            'text': final_message,
            'parse_mode': 'Markdown'
        })
        
        if not message_response.ok:
            print(f"[WARNING] Не удалось отправить итоговый ответ: {message_response.text}")
        
        # 3. Закрываем тему
        close_url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/closeForumTopic'
        close_response = requests.post(close_url, json={
            'chat_id': topic.chat_id,
            'message_thread_id': topic.message_thread_id
        })
        
        if not close_response.ok:
            error_data = close_response.json()
            return jsonify({
                'success': False,
                'error': f'Ошибка закрытия темы: {error_data.get("description", "Неизвестная ошибка")}'
            }), 500
        
        # 4. Обновляем статус вопроса
        question.status = 'ARCHIVED'
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Вопрос перемещен в архив'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@questions_bp.route("/<int:question_id>", methods=["GET", "POST"])
def question_detail(question_id: int):
    """Детальная страница вопроса с полным текстом и итоговым ответом."""
    
    # Получаем роль пользователя
    user_id = session.get("user_id")
    user_role = None
    if user_id:
        db_temp = SessionLocal()
        try:
            user = db_temp.query(User).filter_by(id=user_id).first()
            if user:
                user_role = user.role
        finally:
            db_temp.close()
    
    # Обработка POST запроса (создание или редактирование)
    if request.method == "POST":
        # Проверяем права
        if not user_role or user_role < 1:
            return "Недостаточно прав", 403
        
        db = SessionLocal()
        try:
            # Если question_id == 0, создаем новый вопрос
            if question_id == 0:
                title = request.form.get('title', '').strip() or None
                body = request.form.get('body', '').strip()
                
                print(f"[DEBUG] Creating question - title: '{title}', body length: {len(body)}")
                
                # Автоматически генерируем заголовок если не указан
                if not title and body:
                    print(f"[DEBUG] Generating title for body: {body[:100]}...")
                    title = generate_title_with_ai(body)
                    print(f"[AI Title] Generated: {title}")
                else:
                    print(f"[DEBUG] Skipping title generation - title exists or body empty")
                
                question = Question(
                    title=title,
                    body=body,
                    status=request.form.get('status', 'VOTING')
                )
                db.add(question)
                db.flush()  # Получаем ID для связей
                new_question_id = question.id
            else:
                # Редактируем существующий вопрос
                question = db.query(Question).filter_by(id=question_id).first()
                if not question:
                    db.close()
                    return "Вопрос не найден", 404
                
                # Обновляем поля вопроса
                new_title = request.form.get('title', '').strip() or None
                new_body = request.form.get('body', '').strip()
                
                print(f"[DEBUG] Editing question {question_id} - title: '{new_title}', body length: {len(new_body)}")
                
                # Автоматически генерируем заголовок если не указан
                if not new_title and new_body:
                    print(f"[DEBUG] Generating title for edited question")
                    new_title = generate_title_with_ai(new_body)
                    print(f"[AI Title] Generated: {new_title}")
                else:
                    print(f"[DEBUG] Skipping title generation - title exists or body empty")
                
                question.title = new_title
                question.body = new_body
                question.status = request.form.get('status', 'VOTING')
                new_question_id = question_id
            
            # Обновляем связи с модулями
            selected_modules = request.form.getlist('modules')
            
            # Удаляем старые связи в любом случае (для редактирования)
            if question_id != 0:
                db.query(QuestionStepikModule).filter_by(question_id=question_id).delete()
            
            # Создаем новые связи если модули выбраны
            for module_id in selected_modules:
                link = QuestionStepikModule(
                    question_id=new_question_id,
                    module_id=int(module_id)
                )
                db.add(link)
            
            # Обновляем или создаём итоговый ответ
            answer_text = request.form.get('answer', '').strip()
            sources_text = request.form.get('sources', '').strip()
            
            if answer_text:
                # Преобразуем sources в JSON формат
                sources_json = None
                if sources_text and sources_text.lower() != 'null':
                    sources_json = {"text": sources_text}
                
                # Генерируем краткое резюме автоматически
                print(f"[DEBUG] Generating summary for answer, length: {len(answer_text)}")
                answer_summary = generate_summary_with_ai(answer_text)
                print(f"[AI Summary] Generated: {answer_summary[:100]}...")
                
                # Если есть answer, создаём/обновляем запись
                answer = db.query(QuestionAnswer).filter_by(question_id=new_question_id).first()
                if not answer:
                    answer = QuestionAnswer(
                        question_id=new_question_id,
                        author_id=user_id,
                        summary=answer_summary,
                        answer=answer_text,
                        sources=sources_json
                    )
                    db.add(answer)
                else:
                    # Обновляем существующий ответ
                    answer.summary = answer_summary
                    answer.answer = answer_text
                    answer.sources = sources_json
                    answer.updated_at = datetime.utcnow()
            
            db.commit()
            db.close()
            
            # Редирект обратно на просмотр
            return redirect(url_for('questions.question_detail', question_id=new_question_id))
            
        except Exception as e:
            db.rollback()
            db.close()
            return f"Ошибка сохранения: {str(e)}", 500
    
    # GET запрос - показываем вопрос или форму создания
    
    db = SessionLocal()
    try:
        # Если question_id == 0, показываем форму создания нового вопроса
        if question_id == 0:
            if not user_role or user_role < 1:
                return "Недостаточно прав для создания вопроса", 403
            
            # Получаем все модули для выбора
            all_modules = db.query(StepikModule).order_by(StepikModule.position).all()
            
            # Создаем пустой объект для совместимости с шаблоном
            class EmptyQuestion:
                id = 0
                title = ''
                body = ''
                status = 'VOTING'
                created_at = datetime.utcnow()
            
            question = EmptyQuestion()
            modules = []
            selected_module_ids = []
            answer = None
            votes_count = 0
            telegram_link = None
            messages_count = 0
        else:
            # Показываем существующий вопрос
            question = db.query(Question).filter_by(id=question_id).first()
            if not question:
                return "Вопрос не найден", 404
            
            # Получаем модули вопроса
            modules = (
                db.query(StepikModule)
                .join(QuestionStepikModule)
                .filter(QuestionStepikModule.question_id == question_id)
                .order_by(StepikModule.position)
                .all()
            )
            
            # Получаем все доступные модули для редактирования
            all_modules = db.query(StepikModule).order_by(StepikModule.position).all()
            selected_module_ids = [m.id for m in modules]
            
            # Получаем итоговый ответ
            answer = db.query(QuestionAnswer).filter_by(question_id=question_id).first()
            
            # Получаем количество голосов из поля
            votes_count = question.votes_count
            
            # Получаем ссылку на Telegram
            telegram_link = None
            messages_count = 0
            if question.status in ['POSTED', 'CLOSED', 'ARCHIVED']:
                topic = db.query(TelegramTopic).filter_by(question_id=question_id).first()
                if topic:
                    telegram_link = f"https://t.me/c/{str(topic.chat_id)[4:]}/{topic.message_thread_id}"
                    messages_count = topic.messages_count or 0
                    print(f"[DEBUG] Question {question_id}: messages_count = {messages_count}")
        
        # Простой шаблон для детальной страницы
        detail_template = """
        <!doctype html>
        <html lang="ru">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{{ question.title or 'Вопрос #' + question.id|string }}</title>
          <script src="https://telegram.org/js/telegram-web-app.js"></script>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
              line-height: 1.6;
              background: #f5f5f5;
            }
            .back-link { display: inline-block; margin-bottom: 20px; color: #667eea; text-decoration: none; }
            .back-link:hover { text-decoration: underline; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
            .modules { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
            .module-badge { background: #e3f2fd; color: #1976d2; padding: 6px 12px; border-radius: 12px; font-size: 13px; }
            .question-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
            .status-badge { padding: 6px 14px; border-radius: 12px; font-size: 13px; font-weight: 600; white-space: nowrap; }
            .status-voting { background: #fff3e0; color: #f57c00; }
            .status-scheduled { background: #e1f5fe; color: #0288d1; }
            .status-posted { background: #e8f5e9; color: #388e3c; }
            .status-closed { background: #f3e5f5; color: #7b1fa2; }
            .status-archived { background: #ede7f6; color: #512da8; }
            h1 { margin-bottom: 16px; color: #222; }
            .meta { color: #999; font-size: 14px; margin-bottom: 24px; }
            .body { white-space: pre-wrap; margin-bottom: 24px; color: #333; }
            .answer-section { background: #f9fbe7; border-left: 4px solid #9ccc65; padding: 20px; border-radius: 4px; margin-top: 24px; }
            .answer-section h2 { color: #558b2f; margin-bottom: 12px; }
            .telegram-btn { display: inline-block; padding: 12px 24px; background: #0088cc; color: white; text-decoration: none; border-radius: 8px; margin-top: 16px; border: none; cursor: pointer; }
            .telegram-btn:hover { background: #006699; }
            .edit-btn { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; margin-top: 16px; }
            .edit-btn:hover { background: #5568d3; }
            .close-discussion-btn { display: inline-block; padding: 10px 20px; background: #f44336; color: white; text-decoration: none; border-radius: 8px; margin-top: 16px; border: none; cursor: pointer; }
            .close-discussion-btn:hover { background: #d32f2f; }
            .archive-btn { display: inline-block; padding: 10px 20px; background: #9c27b0; color: white; text-decoration: none; border-radius: 8px; margin-top: 16px; border: none; cursor: pointer; }
            .archive-btn:hover { background: #7b1fa2; }
            .action-buttons { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; gap: 12px; }
            .edit-form { background: #f9f9f9; padding: 24px; border-radius: 8px; margin-top: 24px; border: 2px solid #667eea; }
            .edit-form h2 { margin-top: 0; color: #667eea; }
            .form-group { margin-bottom: 16px; }
            .form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; }
            .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; font-family: inherit; }
            .form-group textarea { min-height: 150px; resize: vertical; }
            .form-actions { display: flex; gap: 12px; margin-top: 20px; }
            .btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 600; }
            .btn-primary { background: #667eea; color: white; }
            .btn-primary:hover { background: #5568d3; }
            .btn-secondary { background: #e0e0e0; color: #333; }
            .btn-secondary:hover { background: #d0d0d0; }
            .modules-selector { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
            .module-checkbox-label { cursor: pointer; }
            .module-checkbox-badge { display: inline-block; padding: 6px 12px; background: #e0e0e0; color: #666; border-radius: 12px; font-size: 13px; transition: all 0.2s; user-select: none; }
            .module-checkbox-label.selected .module-checkbox-badge { background: #e3f2fd; color: #1976d2; font-weight: 600; }
            .module-checkbox-label:hover .module-checkbox-badge { background: #d0d0d0; }
            .module-checkbox-label.selected:hover .module-checkbox-badge { background: #bbdefb; }
          </style>
        </head>
        <body>
          <a href="{{ url_for('questions.list_questions') }}" class="back-link" id="back-link">← Назад к списку вопросов</a>
          
          {% if question.id != 0 %}
          <div class="card">
            <div class="modules">
              {% for module in modules %}
                <span class="module-badge">{{ module.short_title or module.title }}</span>
              {% endfor %}
            </div>
            
            <div class="question-header">
              <div>
                {% if question.title %}
                  <h1 style="margin: 0;">{{ question.title }}</h1>
                {% else %}
                  <h1 style="margin: 0;">Вопрос #{{ question.id }}</h1>
                {% endif %}
              </div>
              <span class="status-badge status-{{ question.status.lower() }}">
                {{ get_status_label(question.status) }}
              </span>
            </div>
            
            <div class="meta">
              ❤️ {{ votes_count }} голосов | 📅 {{ question.created_at.strftime('%d.%m.%Y %H:%M') }}
            </div>
            
            <div class="body">{{ question.body }}</div>
            
            {% if answer %}
              <div class="answer-section">
                <h2>✅ Итоговый ответ</h2>
                
                {% if answer.summary %}
                  <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #558b2f;">
                    <strong style="color: #558b2f;">Краткий ответ:</strong>
                    <p style="margin: 8px 0 0 0;">{{ answer.summary }}</p>
                  </div>
                {% endif %}
                
                <div style="white-space: pre-wrap;">{{ answer.answer }}</div>
                
                {% if answer.sources %}
                  <p style="margin-top: 16px; font-size: 14px; color: #666;">
                    📚 Источники: {{ answer.sources.text if answer.sources.text else answer.sources }}
                  </p>
                {% endif %}
              </div>
            {% endif %}
            
            {% if user_role and user_role >= 1 %}
              <div class="action-buttons">
                <a href="#edit" class="edit-btn" onclick="document.getElementById('edit-form').style.display='block'; this.parentElement.style.display='none'; return false;">
                  ✏️ Редактировать
                </a>
                
                {% if telegram_link and question.status == 'POSTED' %}
                  <a href="{{ telegram_link }}" target="_blank" class="telegram-btn">
                    💬 Обсуждение ({{ messages_count - 1 if messages_count > 0 else 0 }})
                  </a>
                  <button onclick="closeDiscussion({{ question.id }})" class="close-discussion-btn" id="close-btn">
                    🔒 Закрыть обсуждение
                  </button>
                {% elif telegram_link and question.status == 'CLOSED' %}
                  <a href="{{ telegram_link }}" target="_blank" class="telegram-btn">
                    💬 Обсуждение в Telegram ({{ messages_count - 1 if messages_count > 0 else 0 }})
                  </a>
                  <button onclick="archiveQuestion({{ question.id }})" class="archive-btn" id="archive-btn">
                    📦 В архив
                  </button>
                {% elif telegram_link %}
                  <a href="{{ telegram_link }}" target="_blank" class="telegram-btn">
                    💬 Обсуждение в Telegram ({{ messages_count - 1 if messages_count > 0 else 0 }})
                  </a>
                {% elif question.status == 'VOTING' %}
                  <button onclick="publishQuestion({{ question.id }})" class="telegram-btn" id="publish-btn" style="background: #26a69a;">
                    📢 Опубликовать в Telegram
                  </button>
                {% endif %}
              </div>
            {% elif telegram_link %}
              <a href="{{ telegram_link }}" target="_blank" class="telegram-btn">
                💬 Обсуждение в Telegram ({{ messages_count - 1 if messages_count > 0 else 0 }})
              </a>
            {% endif %}
          </div>
          {% endif %}
          
          {% if user_role and user_role >= 1 %}
          <div id="edit-form" class="edit-form" style="display: {% if question.id == 0 or '#edit' in request.url %}block{% else %}none{% endif %};">
            <h2>{% if question.id == 0 %}Создание нового вопроса{% else %}Редактирование вопроса{% endif %}</h2>
            <form method="post" action="{{ url_for('questions.question_detail', question_id=question.id) }}">
              <div class="form-group">
                <label for="body">Текст вопроса:</label>
                <textarea id="body" name="body" required>{{ question.body }}</textarea>
              </div>
              
              <div class="form-group">
                <label for="title">Краткий текст (для автозаполнения оставьте пустым):</label>
                <input type="text" id="title" name="title" value="{{ question.title or '' }}">
                <small style="color: #666;">Автоматически создается через AI на основе текста вопроса</small>
              </div>
              
              <div class="form-group">
                <label for="status">Статус:</label>
                <select id="status" name="status" onchange="toggleAnswerSection()">
                  <option value="VOTING" {% if question.status == 'VOTING' %}selected{% endif %}>В голосовании</option>
                  <option value="POSTED" {% if question.status == 'POSTED' %}selected{% endif %}>В обсуждении</option>
                  <option value="CLOSED" {% if question.status == 'CLOSED' %}selected{% endif %}>Закрыто</option>
                  <option value="ARCHIVED" {% if question.status == 'ARCHIVED' %}selected{% endif %}>Архив</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Разделы курса:</label>
                <div class="modules-selector">
                  {% for module in all_modules %}
                    <label class="module-checkbox-label {% if module.id in selected_module_ids %}selected{% endif %}" data-module-id="{{ module.id }}">
                      <input type="checkbox" name="modules" value="{{ module.id }}" {% if module.id in selected_module_ids %}checked{% endif %} style="display: none;">
                      <span class="module-checkbox-badge">{{ module.short_title or module.title }}</span>
                    </label>
                  {% endfor %}
                </div>
              </div>
              
              <div id="answer-section" style="display: {% if question.status in ['CLOSED', 'ARCHIVED'] %}block{% else %}none{% endif %};">
                <hr style="margin: 24px 0; border: none; border-top: 1px solid #ddd;">
                
                <h3 style="color: #558b2f; margin-bottom: 16px;">Итоговый ответ</h3>
                
                <div class="form-group">
                  <label for="answer">Полный ответ:</label>
                  <textarea id="answer" name="answer" style="min-height: 200px;">{{ answer.answer if answer else '' }}</textarea>
                  <small style="color: #666;">Подробный структурированный ответ после обсуждения</small>
                </div>
                
                <div class="form-group">
                  <label for="summary">Краткий ответ (для автозаполнения оставьте пустым):</label>
                  <textarea id="summary" name="summary" style="min-height: 80px;">{{ answer.summary if answer else '' }}</textarea>
                  <small style="color: #666;">Автоматически создается через AI на основе полного ответа</small>
                </div>
                
                <div class="form-group">
                  <label for="sources">Источники (ссылки на уроки, сообщения):</label>
                  <input type="text" id="sources" name="sources" value="{{ answer.sources.text if (answer and answer.sources and answer.sources.text) else '' }}" placeholder="Урок 10, сообщение в форуме, https://...">
                  <small style="color: #666;">Укажите источники информации для ответа</small>
                </div>
              </div>
              
              <div class="form-actions">
                <button type="submit" class="btn btn-primary">💾 Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="document.getElementById('edit-form').style.display='none'; const actionButtons = document.querySelector('.action-buttons'); if (actionButtons) actionButtons.style.display='flex';">Отмена</button>
              </div>
            </form>
          </div>
          {% endif %}
          
          <script>
            // Публикация вопроса в Telegram
            async function publishQuestion(questionId) {
              const btn = document.getElementById('publish-btn');
              if (!btn) return;
              
              const originalText = btn.innerHTML;
              btn.disabled = true;
              btn.innerHTML = '⏳ Публикуем...';
              
              try {
                const response = await fetch(`/questions/${questionId}/publish`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  }
                });
                
                const data = await response.json();
                
                if (data.success) {
                  btn.innerHTML = '✅ Опубликовано!';
                  btn.style.background = '#4caf50';
                  
                  // Перезагружаем страницу через 1 секунду
                  setTimeout(() => {
                    window.location.reload();
                  }, 1000);
                } else {
                  alert('Ошибка: ' + (data.error || 'Не удалось опубликовать'));
                  btn.disabled = false;
                  btn.innerHTML = originalText;
                }
              } catch (error) {
                alert('Ошибка сети: ' + error.message);
                btn.disabled = false;
                btn.innerHTML = originalText;
              }
            }
            
            // Закрытие обсуждения в Telegram
            async function closeDiscussion(questionId) {
              if (!confirm('Вы уверены, что хотите закрыть обсуждение? Это действие нельзя отменить.')) {
                return;
              }
              
              const btn = document.getElementById('close-btn');
              const originalText = btn.innerHTML;
              btn.disabled = true;
              btn.innerHTML = '⏳ Закрываем...';
              
              try {
                const response = await fetch(`/questions/${questionId}/close-discussion`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  }
                });
                
                const data = await response.json();
                
                if (data.success) {
                  btn.innerHTML = '✅ Закрыто!';
                  btn.style.background = '#4caf50';
                  
                  // Перезагружаем страницу через 1 секунду
                  setTimeout(() => {
                    window.location.reload();
                  }, 1000);
                } else {
                  alert('Ошибка: ' + (data.error || 'Не удалось закрыть обсуждение'));
                  btn.disabled = false;
                  btn.innerHTML = originalText;
                }
              } catch (error) {
                alert('Ошибка сети: ' + error.message);
                btn.disabled = false;
                btn.innerHTML = originalText;
              }
            }
            
            // Архивирование вопроса
            async function archiveQuestion(questionId) {
              if (!confirm('Вопрос будет перемещен в архив. Убедитесь, что итоговый ответ заполнен. Продолжить?')) {
                return;
              }
              
              const btn = document.getElementById('archive-btn');
              const originalText = btn.innerHTML;
              btn.disabled = true;
              btn.innerHTML = '⏳ Архивируем...';
              
              try {
                const response = await fetch(`/questions/${questionId}/archive`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  }
                });
                
                const data = await response.json();
                
                if (data.success) {
                  btn.innerHTML = '✅ В архиве!';
                  btn.style.background = '#4caf50';
                  
                  // Перезагружаем страницу через 1 секунду
                  setTimeout(() => {
                    window.location.reload();
                  }, 1000);
                } else {
                  alert('Ошибка: ' + (data.error || 'Не удалось архивировать'));
                  btn.disabled = false;
                  btn.innerHTML = originalText;
                }
              } catch (error) {
                alert('Ошибка сети: ' + error.message);
                btn.disabled = false;
                btn.innerHTML = originalText;
              }
            }
            
            // Показ/скрытие раздела итогового ответа в зависимости от статуса
            function toggleAnswerSection() {
              const status = document.getElementById('status').value;
              const answerSection = document.getElementById('answer-section');
              
              if (status === 'CLOSED' || status === 'ARCHIVED') {
                answerSection.style.display = 'block';
              } else {
                answerSection.style.display = 'none';
              }
            }
            
            // Toggle модулей при клике
            document.addEventListener('DOMContentLoaded', function() {
              document.querySelectorAll('.module-checkbox-label').forEach(label => {
                label.addEventListener('click', function(e) {
                  e.preventDefault(); // Предотвращаем автоматическое переключение label
                  
                  const checkbox = this.querySelector('input[type="checkbox"]');
                  checkbox.checked = !checkbox.checked;
                  this.classList.toggle('selected');
                });
              });
            });
            
            // Проверяем, открыто ли в Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
              const tg = window.Telegram.WebApp;
              tg.ready();
              tg.expand();
              
              // Меняем ссылку "Назад" на Mini App версию
              const backLink = document.getElementById('back-link');
              if (backLink) {
                backLink.href = '{{ url_for("questions.miniapp") }}';
              }
              
              // Применяем цветовую схему Telegram
              if (tg.themeParams.bg_color) {
                document.body.style.background = tg.themeParams.bg_color;
              }
            }
          </script>
        </body>
        </html>
        """
        
        return render_template_string(
            detail_template,
            question=question,
            modules=modules,
            all_modules=all_modules,
            selected_module_ids=selected_module_ids,
            answer=answer,
            votes_count=votes_count,
            telegram_link=telegram_link,
            messages_count=messages_count,
            user_role=user_role,
            get_status_label=get_status_label
        )
        
    finally:
        db.close()


# ============================================================================
# TELEGRAM MINI APP
# ============================================================================

MINIAPP_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Вопросы курса</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --tg-theme-bg-color: #ffffff;
      --tg-theme-text-color: #000000;
      --tg-theme-hint-color: #999999;
      --tg-theme-link-color: #2481cc;
      --tg-theme-button-color: #2481cc;
      --tg-theme-button-text-color: #ffffff;
      --tg-theme-secondary-bg-color: #f4f4f5;
    }
    
    * { 
      box-sizing: border-box; 
      margin: 0; 
      padding: 0; 
      -webkit-tap-highlight-color: transparent;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--tg-theme-bg-color);
      color: var(--tg-theme-text-color);
      line-height: 1.5;
      padding: 0;
      margin: 0;
      overflow-x: hidden;
    }
    
    .container {
      padding: 8px;
      max-width: 100%;
    }
    
    /* Фильтры компактные */
    .filters {
      background: var(--tg-theme-secondary-bg-color);
      border-radius: 8px;
      padding: 8px;
      margin-bottom: 8px;
    }
    
    .filter-row {
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .filter-row:last-child {
      margin-bottom: 0;
    }
    
    .filter-label {
      font-weight: 600;
      font-size: 11px;
      color: var(--tg-theme-hint-color);
      white-space: nowrap;
      flex-shrink: 0;
    }
    
    .filter-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      flex: 1;
    }
    
    .filter-btn {
      padding: 3px 8px;
      border: none;
      background: transparent;
      border-radius: 10px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
      text-decoration: none;
      color: var(--tg-theme-link-color);
      display: inline-block;
      white-space: nowrap;
    }
    
    .filter-btn.active {
      background: var(--tg-theme-button-color);
      color: var(--tg-theme-button-text-color);
      font-weight: 600;
    }
    
    /* Карточки */
    .questions-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-bottom: 60px;
    }
    
    .question-card {
      background: var(--tg-theme-secondary-bg-color);
      border-radius: 8px;
      padding: 10px;
      transition: opacity 0.2s;
    }
    
    .question-card:active {
      opacity: 0.7;
    }
    
    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 6px;
      gap: 8px;
    }
    
    .question-header-left {
      flex: 1;
      min-width: 0;
    }
    
    .question-header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    
    .question-modules {
      display: flex;
      flex-wrap: wrap;
      gap: 3px;
      flex: 1;
    }
    
    .module-badge {
      background: var(--tg-theme-button-color);
      color: var(--tg-theme-button-text-color);
      padding: 2px 6px;
      border-radius: 8px;
      font-size: 10px;
      font-weight: 500;
      opacity: 0.8;
    }
    
    .status-badge {
      padding: 2px 8px;
      border-radius: 8px;
      font-size: 10px;
      font-weight: 600;
      white-space: nowrap;
      flex-shrink: 0;
    }
    
    .status-voting { background: #fff3e0; color: #f57c00; }
    .status-scheduled { background: #e1f5fe; color: #0288d1; }
    .status-posted { background: #e8f5e9; color: #388e3c; }
    .status-closed { background: #f3e5f5; color: #7b1fa2; }
    .status-archived { background: #ede7f6; color: #512da8; }
    
    .question-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--tg-theme-text-color);
      margin-bottom: 4px;
      line-height: 1.3;
    }
    
    .question-body {
      color: var(--tg-theme-text-color);
      font-size: 14px;
      line-height: 1.4;
    }
    
    .vote-button {
      display: flex;
      align-items: center;
      gap: 4px;
      background: var(--tg-theme-bg-color);
      border: none;
      cursor: pointer;
      font-size: 14px;
      padding: 4px 8px;
      border-radius: 12px;
      transition: all 0.2s;
      color: var(--tg-theme-text-color);
      flex-shrink: 0;
    }
    
    .vote-button:active {
      transform: scale(0.95);
    }
    
    .vote-button.voted {
      color: #e91e63;
    }
    
    .vote-button.voted .heart {
      animation: heartbeat 0.3s;
    }
    
    @keyframes heartbeat {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.3); }
    }
    
    .question-meta {
      display: flex;
      gap: 10px;
      font-size: 12px;
      color: var(--tg-theme-hint-color);
    }
    
    .summary-block {
      background: rgba(156, 204, 101, 0.1);
      border-left: 3px solid #9ccc65;
      padding: 10px;
      margin-top: 10px;
      border-radius: 6px;
    }
    
    .summary-block strong {
      color: #558b2f;
      display: block;
      margin-bottom: 4px;
      font-size: 12px;
    }
    
    .summary-block p {
      font-size: 12px;
      line-height: 1.4;
      color: var(--tg-theme-text-color);
    }
    
    .read-more-btn {
      display: inline-block;
      margin-top: 6px;
      color: var(--tg-theme-link-color);
      text-decoration: none;
      font-weight: 600;
      font-size: 12px;
    }
    
    .telegram-link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-top: 8px;
      padding: 6px 10px;
      background: var(--tg-theme-button-color);
      color: var(--tg-theme-button-text-color);
      text-decoration: none;
      border-radius: 8px;
      font-size: 12px;
    }
    
    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--tg-theme-hint-color);
    }
    
    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
    
    .loading {
      text-align: center;
      padding: 40px 20px;
      color: var(--tg-theme-hint-color);
    }
    
    .spinner {
      border: 3px solid var(--tg-theme-secondary-bg-color);
      border-top: 3px solid var(--tg-theme-button-color);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    /* Компактность на малых экранах */
    @media (max-width: 360px) {
      .container { padding: 8px; }
      .question-card { padding: 12px; }
      .filter-btn { font-size: 12px; padding: 5px 10px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Фильтры -->
    <div class="filters">
      <!-- Строка 1: Темы -->
      <div class="filter-row">
        <div class="filter-label">📌</div>
        <div class="filter-buttons" id="topic-filters">
          <a href="#" class="filter-btn active" data-topic="all">Все</a>
        </div>
      </div>
      
      <!-- Строка 2: Статусы -->
      <div class="filter-row">
        <div class="filter-label">🔖</div>
        <div class="filter-buttons" id="status-filters">
          <a href="#" class="filter-btn active" data-status="all">Все</a>
          <a href="#" class="filter-btn" data-status="VOTING">Голосование</a>
          <a href="#" class="filter-btn" data-status="POSTED">Обсуждение</a>
          <a href="#" class="filter-btn" data-status="CLOSED">Закрыто</a>
          <a href="#" class="filter-btn" data-status="ARCHIVED">Архив</a>
        </div>
      </div>
      
      <!-- Строка 3: Период -->
      <div class="filter-row">
        <div class="filter-label">📅</div>
        <div class="filter-buttons" id="period-filters">
          <a href="#" class="filter-btn active" data-period="all">Все</a>
          <a href="#" class="filter-btn" data-period="last30">30 вопросов</a>
          <a href="#" class="filter-btn" data-period="week">Неделя</a>
          <a href="#" class="filter-btn" data-period="month">Месяц</a>
        </div>
      </div>
    </div>
    
    <!-- Список вопросов -->
    <div id="questions-container">
      <div class="loading">
        <div class="spinner"></div>
        <p>Загрузка вопросов...</p>
      </div>
    </div>
  </div>
  
  <script>
    // Инициализация Telegram WebApp
    const tg = window.Telegram.WebApp;
    tg.expand();
    
    // Применяем цветовую схему Telegram
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f4f4f5');
    
    // Состояние фильтров
    let currentFilters = {
      topic: 'all',
      status: 'all',
      period: 'all'
    };
    
    // Получаем initData для авторизации
    const initData = tg.initData;
    const user = tg.initDataUnsafe?.user;
    
    console.log('Telegram User:', user);
    console.log('Init Data:', initData);
    
    // Функция загрузки вопросов
    async function loadQuestions() {
      const container = document.getElementById('questions-container');
      container.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <p>Загрузка вопросов...</p>
        </div>
      `;
      
      try {
        const params = new URLSearchParams({
          topic: currentFilters.topic,
          status: currentFilters.status,
          period: currentFilters.period
        });
        
        console.log('[MiniApp] Loading questions with params:', params.toString());
        console.log('[MiniApp] initData length:', initData ? initData.length : 0);
        
        const response = await fetch(`/questions/api/questions?${params}`, {
          headers: {
            'X-Telegram-Init-Data': initData
          }
        });
        
        console.log('[MiniApp] Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('[MiniApp] Error response:', errorText);
          throw new Error(`Failed to load questions: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('[MiniApp] Questions loaded:', data.questions ? data.questions.length : 0);
        renderQuestions(data.questions);
        
      } catch (error) {
        console.error('[MiniApp] Error loading questions:', error);
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">❌</div>
            <h3>Ошибка загрузки</h3>
            <p>Не удалось загрузить вопросы.</p>
            <p style="font-size: 12px; color: #888;">${error.message}</p>
          </div>
        `;
        tg.showAlert('Ошибка: ' + error.message);
      }
    }
    
    // Функция рендеринга вопросов
    function renderQuestions(questions) {
      const container = document.getElementById('questions-container');
      
      if (questions.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🤔</div>
            <h3>Вопросов не найдено</h3>
            <p>Попробуйте изменить фильтры</p>
          </div>
        `;
        return;
      }
      
      const html = `
        <div class="questions-list">
          ${questions.map(q => `
            <div class="question-card">
              <div class="question-header">
                <div class="question-header-left">
                  <div class="question-modules">
                    ${q.modules.map(m => `<span class="module-badge" onclick="filterByModule(${m.id})">${m.title}</span>`).join('')}
                  </div>
                </div>
                <div class="question-header-right">
                  <span class="status-badge status-${q.status.toLowerCase()}" onclick="filterByStatus('${q.status}')">${q.status_label}</span>
                  <button class="vote-button ${q.my_vote ? 'voted' : ''}" 
                          data-question-id="${q.id}" 
                          onclick="toggleVote(${q.id}, this)">
                    <span class="heart">${q.my_vote ? '❤️' : '🤍'}</span>
                    <span class="vote-count">${q.votes_count}</span>
                  </button>
                </div>
              </div>
              
              ${q.title ? `<div class="question-title">${q.title}</div>` : ''}
              
              <div class="question-body">${q.body_preview}</div>
              
              ${q.summary ? `
                <div class="summary-block">
                  <strong>✅ Итог</strong>
                  <p>${q.summary}</p>
                  <a href="/questions/${q.id}" class="read-more-btn">Читать полностью →</a>
                </div>
              ` : ''}
              
              ${q.telegram_link ? `
                <a href="${q.telegram_link}" class="telegram-link">
                  💬 Перейти к обсуждению в Telegram (${q.messages_count > 0 ? q.messages_count - 1 : 0})
                </a>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
      
      container.innerHTML = html;
    }
    
    // Функция голосования
    async function toggleVote(questionId, button) {
      const heart = button.querySelector('.heart');
      const voteCount = button.querySelector('.vote-count');
      const wasVoted = button.classList.contains('voted');
      
      // Оптимистичное обновление UI
      button.classList.toggle('voted');
      heart.textContent = button.classList.contains('voted') ? '❤️' : '🤍';
      
      // Haptic feedback
      tg.HapticFeedback.impactOccurred('light');
      
      try {
        const response = await fetch(`/questions/${questionId}/vote`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Telegram-Init-Data': initData
          }
        });
        
        if (!response.ok) {
          throw new Error('Vote failed');
        }
        
        const data = await response.json();
        
        // Обновляем счетчик
        voteCount.textContent = data.votes_count;
        button.classList.toggle('voted', data.liked);
        heart.textContent = data.liked ? '❤️' : '🤍';
        
        // Haptic feedback при успехе
        tg.HapticFeedback.notificationOccurred('success');
        
      } catch (error) {
        console.error('Vote error:', error);
        // Откатываем изменения при ошибке
        button.classList.toggle('voted', wasVoted);
        heart.textContent = wasVoted ? '❤️' : '🤍';
        tg.HapticFeedback.notificationOccurred('error');
        tg.showAlert('Ошибка голосования. Попробуйте еще раз.');
      }
    }
    
    // Фильтрация по модулю
    function filterByModule(moduleId) {
      // Проверяем, не выбран ли уже этот фильтр
      if (currentFilters.topic === moduleId.toString()) {
        return; // Ничего не делаем, фильтр уже активен
      }
      
      // Обновляем фильтр
      currentFilters.topic = moduleId.toString();
      
      // Обновляем активную кнопку в фильтрах
      document.querySelectorAll('#topic-filters .filter-btn').forEach(b => b.classList.remove('active'));
      const btn = document.querySelector(`#topic-filters .filter-btn[data-topic="${moduleId}"]`);
      if (btn) btn.classList.add('active');
      
      tg.HapticFeedback.selectionChanged();
      loadQuestions();
    }
    
    // Фильтрация по статусу
    function filterByStatus(status) {
      // Проверяем, не выбран ли уже этот фильтр
      if (currentFilters.status === status) {
        return; // Ничего не делаем, фильтр уже активен
      }
      
      // Обновляем фильтр
      currentFilters.status = status;
      
      // Обновляем активную кнопку в фильтрах
      document.querySelectorAll('#status-filters .filter-btn').forEach(b => b.classList.remove('active'));
      const btn = document.querySelector(`#status-filters .filter-btn[data-status="${status}"]`);
      if (btn) btn.classList.add('active');
      
      tg.HapticFeedback.selectionChanged();
      loadQuestions();
    }
    
    // Форматирование даты
    function formatDate(dateString) {
      const date = new Date(dateString);
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}.${month}.${year}`;
    }
    
    // Обработчики фильтров
    function setupFilters() {
      // Topic filters
      document.querySelectorAll('#topic-filters .filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          document.querySelectorAll('#topic-filters .filter-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentFilters.topic = btn.dataset.topic;
          loadQuestions();
          tg.HapticFeedback.selectionChanged();
        });
      });
      
      // Status filters
      document.querySelectorAll('#status-filters .filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          document.querySelectorAll('#status-filters .filter-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentFilters.status = btn.dataset.status;
          loadQuestions();
          tg.HapticFeedback.selectionChanged();
        });
      });
      
      // Period filters
      document.querySelectorAll('#period-filters .filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          document.querySelectorAll('#period-filters .filter-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentFilters.period = btn.dataset.period;
          loadQuestions();
          tg.HapticFeedback.selectionChanged();
        });
      });
    }
    
    // Загрузка модулей для фильтров
    async function loadModules() {
      try {
        const response = await fetch('/questions/api/modules');
        if (response.ok) {
          const modules = await response.json();
          const topicFilters = document.getElementById('topic-filters');
          
          modules.forEach(module => {
            const btn = document.createElement('a');
            btn.href = '#';
            btn.className = 'filter-btn';
            btn.dataset.topic = module.id;
            btn.textContent = module.title;
            topicFilters.appendChild(btn);
          });
          
          setupFilters();
        }
      } catch (error) {
        console.error('Error loading modules:', error);
      }
    }
    
    // Инициализация
    document.addEventListener('DOMContentLoaded', () => {
      loadModules();
      setupFilters();
      loadQuestions();
      
      // Сообщаем Telegram что приложение готово
      tg.ready();
    });
  </script>
</body>
</html>
"""


@questions_bp.route("/miniapp", methods=["GET"])
def miniapp():
    """Mini App версия для Telegram WebView."""
    return render_template_string(MINIAPP_TEMPLATE)


# ============================================================================
# API ENDPOINTS FOR MINI APP
# ============================================================================

@questions_bp.route("/api/questions", methods=["GET"])
def api_questions():
    """API эндпоинт для получения списка вопросов (для Mini App).
    
    Параметры фильтрации:
      - topic: id модуля или 'all'
      - status: статус вопроса или 'all'
      - period: 'all', 'last30', 'week', 'month', 'year'
        'last30' — последние 30 вопросов (после 'Все время')
    """
    
    print(f"[API] /api/questions called")
    print(f"[API] Headers: {dict(request.headers)}")
    
    # Получаем параметры фильтрации
    topic_filter = request.args.get('topic', 'all')
    status_filter = request.args.get('status', 'all')
    period_filter = request.args.get('period', 'all')
    
    # Получаем initData из заголовка
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    telegram_user_id = None
    
    # Простая валидация: извлекаем user_id из initData
    # ВРЕМЕННО: отключаем строгую валидацию для тестирования
    if init_data:
        try:
            # Парсим initData (формат: key=value&key=value)
            params = dict(item.split('=') for item in init_data.split('&') if '=' in item)
            if 'user' in params:
                import json
                import urllib.parse
                user_data = json.loads(urllib.parse.unquote(params['user']))
                telegram_user_id = user_data.get('id')
                print(f"[API] Extracted telegram_user_id: {telegram_user_id}")
        except Exception as e:
            print(f"[API] Error parsing initData: {e}")
    
    db = SessionLocal()
    try:
        # Базовый запрос для подсчета голосов
        votes_subquery = (
            db.query(
                QuestionVote.question_id,
                func.count(QuestionVote.telegram_user_id).label('votes_count')
            )
            .group_by(QuestionVote.question_id)
            .subquery()
        )
        
        # Основной запрос
        if telegram_user_id:
            my_vote_exists = exists().where(
                QuestionVote.question_id == Question.id,
                QuestionVote.telegram_user_id == telegram_user_id
            )
            
            query = (
                db.query(
                    Question,
                    func.coalesce(votes_subquery.c.votes_count, 0).label('votes_count'),
                    my_vote_exists.label('my_vote')
                )
                .outerjoin(votes_subquery, Question.id == votes_subquery.c.question_id)
            )
        else:
            query = (
                db.query(
                    Question,
                    func.coalesce(votes_subquery.c.votes_count, 0).label('votes_count'),
                    func.cast(False, Integer).label('my_vote')
                )
                .outerjoin(votes_subquery, Question.id == votes_subquery.c.question_id)
            )
        
        # Применяем фильтры
        if topic_filter != 'all':
            query = query.join(
                QuestionStepikModule,
                Question.id == QuestionStepikModule.question_id
            ).filter(QuestionStepikModule.module_id == int(topic_filter))
        
        if status_filter != 'all':
            query = query.filter(Question.status == status_filter)
        
        period_date = get_period_filter(period_filter)
        if period_date:
          query = query.filter(Question.created_at >= period_date)
        # Сортировка
        query = query.order_by(
          func.coalesce(votes_subquery.c.votes_count, 0).desc(),
          Question.created_at.desc()
        )
        if period_filter == 'last30':
          query = query.limit(30)
        
        results = query.all()
        
        # Собираем id всех вопросов
        question_ids = [q.id for q, *_ in results]

        # Получаем все модули для всех вопросов одним запросом
        modules_by_qid = {}
        if question_ids:
          qsm = db.query(QuestionStepikModule).filter(QuestionStepikModule.question_id.in_(question_ids)).all()
          module_ids = list({m.module_id for m in qsm})
          modules = db.query(StepikModule).filter(StepikModule.id.in_(module_ids)).all()
          modules_dict = {m.id: m for m in modules}
          for m in qsm:
            modules_by_qid.setdefault(m.question_id, []).append(modules_dict.get(m.module_id))
          # Сортируем модули по позиции
          for qid in modules_by_qid:
            modules_by_qid[qid] = sorted([mod for mod in modules_by_qid[qid] if mod], key=lambda m: m.position)

        # Получаем все ответы одним запросом
        answers = db.query(QuestionAnswer).filter(QuestionAnswer.question_id.in_(question_ids)).all() if question_ids else []
        answers_by_qid = {a.question_id: a for a in answers}

        # Получаем все Telegram темы одним запросом
        topics = db.query(TelegramTopic).filter(TelegramTopic.question_id.in_(question_ids)).all() if question_ids else []
        topics_by_qid = {t.question_id: t for t in topics}

        questions_data = []
        for question, votes_count, my_vote in results:
          # Модули
          modules = modules_by_qid.get(question.id, [])
          # Итоговый ответ
          answer = answers_by_qid.get(question.id)
          answer_preview = None
          if answer and answer.answer:
            if len(answer.answer) > 300:
              answer_preview = answer.answer[:300] + '...'
            else:
              answer_preview = answer.answer
          # Telegram тема
          telegram_link = None
          messages_count = 0
          topic = topics_by_qid.get(question.id)
          if topic:
            telegram_link = f"https://t.me/c/{str(topic.chat_id)[4:]}/{topic.message_thread_id}"
            messages_count = topic.messages_count or 0
          # Превью текста
          body_preview = question.body[:250] + '...' if len(question.body) > 250 else question.body
          questions_data.append({
            'id': question.id,
            'title': question.title,
            'body_preview': body_preview,
            'status': question.status,
            'status_label': get_status_label(question.status),
            'votes_count': votes_count,
            'my_vote': bool(my_vote),
            'modules': [{'id': m.id, 'title': m.short_title or m.title} for m in modules],
            'summary': answer_preview,
            'telegram_link': telegram_link,
            'messages_count': messages_count,
            'created_at': question.created_at.isoformat()
          })
        
        return jsonify({
            'success': True,
            'questions': questions_data
        })
        
    except Exception as e:
        print(f"[API] Error in api_questions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@questions_bp.route("/api/modules", methods=["GET"])
def api_modules():
    """API эндпоинт для получения списка модулей."""
    
    db = SessionLocal()
    try:
        modules = db.query(StepikModule).order_by(StepikModule.position).all()
        
        return jsonify([
            {'id': m.id, 'title': m.short_title or m.title, 'position': m.position}
            for m in modules
        ])
        
    finally:
        db.close()
