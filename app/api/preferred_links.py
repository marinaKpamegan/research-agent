from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_current_user, get_preferred_link_repository
from app.db.repositories.preferred_link import PreferredLinkRepository
from app.schemas.preferred_link import PreferredLink, PreferredLinkCreate, PreferredLinkUpdate
from app.schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[PreferredLink])
def read_preferred_links(
    current_user: User = Depends(get_current_user),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
):
    return link_repo.get_user_preferred_links(user_id=current_user.id)

@router.post("/", response_model=PreferredLink, status_code=status.HTTP_201_CREATED)
def create_preferred_link(
    link: PreferredLinkCreate,
    current_user: User = Depends(get_current_user),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
):
    return link_repo.create_preferred_link(link=link, user_id=current_user.id)

@router.put("/{link_id}", response_model=PreferredLink)
def update_preferred_link(
    link_id: int,
    link: PreferredLinkUpdate,
    current_user: User = Depends(get_current_user),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
):
    # First check if the link exists and belongs to the user
    db_links = link_repo.get_user_preferred_links(user_id=current_user.id)
    db_link = next((l for l in db_links if l.id == link_id), None)
    
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferred link not found"
        )
    
    return link_repo.update_preferred_link(db_link=db_link, link=link)

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preferred_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
):
    # First check if the link exists and belongs to the user
    db_links = link_repo.get_user_preferred_links(user_id=current_user.id)
    db_link = next((l for l in db_links if l.id == link_id), None)
    
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferred link not found"
        )
    
    link_repo.delete_preferred_link(link_id=link_id)
    return None
