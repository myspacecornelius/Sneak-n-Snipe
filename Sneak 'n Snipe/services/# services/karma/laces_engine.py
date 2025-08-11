"""

"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base

class LacesTransaction(Base):
    """Store in your existing PostgreSQL"""
    __tablename__ = "laces_transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    action_type = Column(String)  # 'spot_bonus', 'verify_bonus', etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(String)  # JSON string

class LacesService:
    """Integrate with existing worker system"""
    
    ACTIONS = {
        'spot_bonus': 50,
        'verify_bonus': 10,
        'knowledge_share': 25,
        'trade_facilitator': 100,
        'good_vibes': 5,
        'daily_checkin': 2,
    }
    
    async def award_laces(self, user_id: str, action: str, metadata: Dict = None):
        """Award LACES tokens"""
        amount = self.ACTIONS.get(action, 0)
        
        # Update user balance in Redis (fast access)
        current = await self.redis_client.hincrby(
            f"user:{user_id}:laces",
            "balance",
            amount
        )
        
        # Log transaction in PostgreSQL (permanent record)
        transaction = LacesTransaction(
            user_id=user_id,
            amount=amount,
            action_type=action,
            metadata=json.dumps(metadata or {})
        )
        self.db.add(transaction)
        self.db.commit()
        
        # Broadcast update via existing WebSocket
        await self.redis_client.publish(
            "laces_updates",
            json.dumps({
                "user_id": user_id,
                "new_balance": current,
                "action": action,
                "amount": amount
            })
        )
