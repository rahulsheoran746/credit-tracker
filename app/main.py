from fastapi import FastAPI
from app.routes import member_routes, transaction_routes, sweet_routes

app = FastAPI()

app.include_router(sweet_routes.router)
app.include_router(member_routes.router)
app.include_router(transaction_routes.router)


@app.get("/")
def read_root():
    return {"message": "Sweet Shop API is Running ✅"}
# from app.db import get_connection
# from app.services.transaction_service import TransactionService

# sample_payload = {
#     "member": {
#         "name": "Rajesh Kumar",
#         "phone": "9876543210",
#         'village': "Village A",
#         'state': "State A",
#         'city': "City A"
#     },
#     "transactions": [
#         {
#             "transaction_type": "sweets",
#             "items": [
#                 {
#                     "item_id": 1,
#                     "name": "Kaju Katli",
#                     "quantity_kg": 2.0,
#                     "amount": 1400.00
#                 },
#                 {
#                     "item_id": 3,
#                     "name": "Motichoor Laddu",
#                     "quantity_kg": 1.2,
#                     "amount": 500.00
#                 }
#             ],
#             "total_amount": 1900.00,
#             "amount_given": 1500.00,
#             "notes": "Bought sweets on credit"
#         },
#         {
#             "transaction_type": "cattle_feed",
#             "items": [
#                 {
#                     "item_id": 1,
#                     "name": "abc",
#                     "quantity_kg": 50.0,
#                     "amount": 1800.00
#                 }
#             ],
#             "total_amount": 1800.00,
#             "amount_given": 1500.00,
#             "notes": "Bought cattle feed  on credit"
#         }
#     ],
#     "transaction_date": "2025-05-21T15:00:00Z",
#     "description": "Transaction for Rajesh Kumar"
# }

# if __name__ == "__main__":
#     conn = get_connection()
#     service = TransactionService(conn)

#     result = service.process_transaction_payload(sample_payload)
#     print(result)

#     conn.commit()
#     conn.close()
