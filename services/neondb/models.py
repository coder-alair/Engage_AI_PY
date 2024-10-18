from sqlalchemy import Column, Index, String, DateTime, Boolean, ForeignKey, Table, Text, Integer, Text, text, ARRAY
import uuid
from sqlalchemy.dialects.postgresql import TIMESTAMP, ENUM, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method


Base = declarative_base()

class MyBase(Base):
    __abstract__ = True
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

class _prisma_migrations(MyBase):
    __tablename__ = '_prisma_migrations'

    id = Column(String, primary_key=True, nullable=False)
    checksum = Column(String, nullable=False)
    finished_at = Column(TIMESTAMP(timezone=True))
    migration_name = Column(String, nullable=False)
    logs = Column(Text)
    rolled_back_at = Column(TIMESTAMP(timezone=True))
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)
    applied_steps_count = Column(Integer, nullable=False)

class Passwordreset(MyBase):
    __tablename__ = 'PasswordReset'

    passwordreset_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    requestTime = Column(TIMESTAMP(precision=3), nullable=False)
    expiryTime = Column(TIMESTAMP(precision=3), nullable=False)
    token = Column(Text, nullable=False)
    userId = Column(Text, ForeignKey('User.user_id', name='PasswordReset_userId_fkey', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    createdAt = Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    user = relationship('User')

    __table_args__ = (Index('PasswordReset_userId_key', 'userId', unique=True),)

class Company(MyBase):
    __tablename__ = 'Company'

    company_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    companyName = Column(Text, nullable=False)
    address1 = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    country = Column(Text, nullable=False)
    postalCode = Column(Text, nullable=False)
    industry = Column(Text, nullable=False)
    bio = Column(Text, nullable=False)
    changeDate = Column(TIMESTAMP(precision=3))
    startDate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    challenges = Column(Text)
    businessArea = Column(Text)
    province = Column(Text)
    state = Column(Text)

class User(MyBase):
    __tablename__ = 'User'

    user_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(Text, nullable=False)
    firstName = Column(Text, nullable=False)
    lastName = Column(Text, nullable=False)
    isAuthenticated = Column(Boolean, nullable=False)
    isValidated = Column(Boolean, nullable=False)
    password = Column(Text, nullable=False)
    companyId = Column(Text, ForeignKey('Company.company_id', name='User_companyId_fkey',onupdate='CASCADE',ondelete='SET NULL'))
    startDate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    changeDate = Column(TIMESTAMP(precision=3), nullable=True)

    jobTitle = Column(Text)
    role = Column(ENUM('USER', 'ADMIN', name='Role'), nullable=False, server_default=text('\'ADMIN\'::"Role"'))

    company = relationship('Company')
    user_subscriptions = relationship('UserSubscription', back_populates="user")

    __table_args__ = (Index('User_email_key', 'email', unique=True),)

class Softwareroles(MyBase):
    __tablename__ = 'SoftwareRoles'

    role_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(precision=3), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP(precision=3), onupdate=func.now())

class _alembic(MyBase):
    __tablename__ = 'alembic_version'

    version_num = Column(String, primary_key=True, nullable=False)

class Resumefiles(MyBase):
    __tablename__ = 'ResumeFiles'

    file_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    filename = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    uploaded_at = Column(TIMESTAMP(precision=3), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    extracted_data = Column(Text)
    user_id = Column(Text, ForeignKey('User.user_id', name="ResumeFiles_user_id_fkey", onupdate='CASCADE', ondelete='SET NULL'))
    user = relationship('User')

class Jobs(MyBase):
    __tablename__ = 'Jobs'

    job_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, ForeignKey('User.user_id', name="Jobs_user_id_fkey", onupdate='CASCADE', ondelete='SET NULL'))
    job_name = Column(Text, nullable=False)
    working_mode = Column(Text, nullable=False, default="")
    salary_range = Column(Text, nullable=False, default="")
    isContract = Column(Boolean, nullable=False, default=False)
    job_description = Column(Text, nullable=False)
    qualifications = Column(ARRAY(Text), nullable=False, default=[])
    experience = Column(ARRAY(Text), nullable=False, default=[])
    technologies = Column(ARRAY(Text), nullable=False, default=[])
    responsibilities = Column(ARRAY(Text), nullable=False, default=[])
    created_at = Column(TIMESTAMP(precision=3), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP(precision=3), onupdate=text('CURRENT_TIMESTAMP'))
    user = relationship('User')

class Locations(MyBase):
    __tablename__ = 'Locations'

    location_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    location_city = Column(Text, nullable=False)
    location_country = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(precision=3), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP(precision=3), onupdate=text('CURRENT_TIMESTAMP'))

class ResumeAnalysis(MyBase):
    __tablename__ = 'ResumeAnalysis'

    analysis_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    candidate_name = Column(Text, nullable=False)
    percent_score = Column(Integer, nullable=False)
    qualifications_percent_score = Column(Integer, nullable=False)
    responsibilities_percent_score = Column(Integer, nullable=False)
    technologies_percent_score = Column(Integer, nullable=False)
    experience_percent_score = Column(Integer, nullable=False)
    brief_analysis = Column(Text, nullable=False)
    interview_points = Column(Text, nullable=False)
    resume_id = Column(Text, ForeignKey('ResumeFiles.file_id',name="ResumeAnalysis_file_id_fkey", onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    job_id = Column(Text, ForeignKey('Jobs.job_id', name="ResumeAnalysis_job_id_fkey", onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    resume = relationship('Resumefiles')
    job = relationship('Jobs')

class Prompts(MyBase):
    __tablename__ = 'Prompts'

    prompt_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    prompt_name = Column(String(36), nullable=False, unique=True)
    system_prompt = Column(Text, nullable=False, server_default="Be a Helpful Assistant")
    user_prompt = Column(Text, nullable=False)

class Subscriptions(MyBase):
    __tablename__ = 'subscriptions'

    subscription_id = Column(Text, primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    subscription_name = Column(Text, nullable=False)
    featuresAvail = Column(JSONB, nullable=False)
    featuresUnavail = Column(JSONB, nullable=False)
    resumesAvailablity = Column(Integer, nullable=False)
    subscription_type = Column(ENUM('MONTHLY', 'ANNUALLY', 'TRIAL', name='SubscriptionType'), nullable=False)
    status = Column(Boolean, nullable=False)
    deletedAt = Column(TIMESTAMP(precision=3), nullable=True)
    createdAt = Column(TIMESTAMP(precision=3), nullable=True)
    updatedAt = Column(TIMESTAMP(precision=3), nullable=True)
    price = Column(Integer, nullable=False)
    product_id = Column(Text, nullable=True)

    user_subscriptions = relationship('UserSubscription', back_populates="subscription")

    def __repr__(self):
            return f"<Subscription(id={self.subscription_id}, type={self.subscription_type}, status={self.status})>"
    
class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'

    user_subscription_id = Column(Text, primary_key=True)
    user_id = Column(Text, ForeignKey('User.user_id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    subscription_id = Column(Text, ForeignKey('subscriptions.subscription_id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    resumes_used = Column(Integer, nullable=False)
    expiry_date = Column(TIMESTAMP(precision=3), nullable=False)
    purchase_history = Column(JSONB, nullable=False)
    createdAt = Column(TIMESTAMP(precision=3), server_default=func.now(), nullable=False)
    updatedAt = Column(TIMESTAMP(precision=3), nullable=False, onupdate=func.now())

    user = relationship("User", back_populates="user_subscriptions")
    subscription = relationship("Subscriptions", back_populates="user_subscriptions")

    def __repr__(self):
        return f"<UserSubscription(id={self.user_subscription_id}, user_id={self.user_id}, subscription_id={self.subscription_id})>"
    
    @hybrid_method
    def use_resume(self, amount=1):
        self.resumes_used += amount
        return self.resumes_used