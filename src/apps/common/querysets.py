from django.db import models


class BusinessQuerySet(models.QuerySet):
    def filter_owner(self, owner):
        """Returns only those that belong to the user and owner and are active."""
        return self.filter(is_deleted=False, owner=owner)

    def filter_by_public_uuid(self, owner, public_uuid: str):
        """Return only the businesses that have this public UUID."""
        return self.filter_owner(owner).filter(public_uuid=public_uuid)

    def for_employee(self, public_uuid: str):
        """Returns the company using the public identifier for the employee."""
        return self.filter(is_deleted=False, is_active=True).filter(
            public_uuid=public_uuid
        )


class EmployeeQuerySet(models.QuerySet):
    def filter_active(self):
        """Filter only those that are active."""
        return self.filter(is_deleted=False, is_active=True)

    def filter_by_business(self, business):
        """It only searches for employees who have a relationship with the company."""
        return self.filter_active().filter(business=business)

    def filter_by_register(self, business, register: str):
        """Filter the employee using register."""
        return self.filter_by_business(business).filter(register=register)
