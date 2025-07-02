from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
import structlog

from app.models.user import User, UserRole
from app.models.auth_schema import UserAuthScheme
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

logger = structlog.get_logger()

class UserService:
    """Enterprise user management service with tenant isolation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str, tenant_id: str) -> Optional[User]:
        """Get user by email within tenant context"""
        return self.db.query(User).filter(
            and_(User.email == email, User.tenant_id == tenant_id)
        ).first()
    
    def get_user_by_id(self, user_id: int, tenant_id: str) -> Optional[User]:
        """Get user by ID within tenant context"""
        return self.db.query(User).filter(
            and_(User.id == user_id, User.tenant_id == tenant_id)
        ).first()
    
    #protect this
    def get_users_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users for a tenant with pagination"""
        return self.db.query(User).filter(
            User.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
    
    def create_user(self, user_data: UserCreate, tenant_id: str, created_by_user_id: Optional[int] = None) -> User:
        """Create new user with audit logging"""
        
     
        existing_user = self.get_user_by_email(user_data.email, tenant_id)
        if existing_user:
            raise ValueError("User with this email already exists in this tenant")
        
       
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,

            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            tenant_id=tenant_id
        )



        
        self.db.add(db_user)
        self.db.flush()  # Get ID without committing

        user_auth = UserAuthScheme(
            user_id=db_user.id,
            hashed_password=hashed_password,
        )

        self.db.add(user_auth)
        
       
        self._create_audit_log(
            event_type="CREATE",
            resource_type="User",
            resource_id=str(db_user.id),
            user_id=created_by_user_id,
            tenant_id=tenant_id,
            new_values={
                "email": user_data.email,
                "role": user_data.role.value,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name
            }
        )
        
        self.db.commit()
        self.db.refresh(db_user)
        
        logger.info("User created", 
                   user_id=db_user.id, 
                   email=user_data.email,
                   tenant_id=tenant_id,
                   created_by=created_by_user_id)
        
        return db_user
    
    def update_user(self, user_id: int, user_data: UserUpdate, tenant_id: str, updated_by_user_id: int) -> Optional[User]:
        """Update user with audit logging"""
        
        user = self.get_user_by_id(user_id, tenant_id)
        if not user:
            return None
        
        
        old_values = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "is_active": user.is_active
        }
        
       
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        
        self._create_audit_log(
            event_type="UPDATE",
            resource_type="User",
            resource_id=str(user.id),
            user_id=updated_by_user_id,
            tenant_id=tenant_id,
            old_values=old_values,
            new_values=update_data
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info("User updated", 
                   user_id=user.id,
                   tenant_id=tenant_id,
                   updated_by=updated_by_user_id,
                   changes=update_data)
        
        return user
    
    def get_user_auth(self, user_id: str) -> Optional[UserAuthScheme]:
        return self.db.query(UserAuthScheme).filter(
            and_(UserAuthScheme.user_id == user_id)
        ).first()
    
    def authenticate_user(self, email: str, password: str, tenant_id: str) -> Optional[User]:
        """Authenticate user with failed attempt tracking"""
        
        user = self.get_user_by_email(email, tenant_id)
        if not user:
            
            return None
        
        user_auth = self.get_user_auth(user.id)
        if not user_auth:
            
            return None
        
        if user_auth.is_locked:
            logger.warning("Login attempt on locked account", 
                          email=email, 
                          tenant_id=tenant_id)
            return None
        
        if not verify_password(password, user_auth.hashed_password):
            
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:  # Lock after 5 failed attempts
                user.is_locked = True
                logger.warning("Account locked due to failed attempts", 
                              email=email, 
                              tenant_id=tenant_id)
            
            self.db.commit()
            return None
        

        if user_auth.failed_login_attempts > 0:
            user_auth.failed_login_attempts = 0
            self.db.commit()
        

        self._create_audit_log(
            event_type="LOGIN",
            resource_type="User",
            resource_id=str(user.id),
            user_id=user.id,
            tenant_id=tenant_id
        )
        
        logger.info("User authenticated successfully", 
                   user_id=user.id,
                   email=email,
                   tenant_id=tenant_id)
        
        return user
    
    def _create_audit_log(self, event_type: str, resource_type: str, resource_id: str, 
                         user_id: Optional[int], tenant_id: str, 
                         old_values: dict = None, new_values: dict = None, **kwargs):
        """Create audit log entry"""
        
        audit_log = AuditLog(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            tenant_id=tenant_id,
            old_values=old_values,
            new_values=new_values,
            **kwargs
        )
        
        self.db.add(audit_log)