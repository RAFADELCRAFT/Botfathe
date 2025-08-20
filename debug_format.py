# Debug del formateo de números
valor = 10000000

# Método actual
valor_formateado = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
valor_str = f"- ${valor_formateado}"
entero, decimal = valor_str[:-3], valor_str[-3:]

print(f"Valor original: {valor}")
print(f"Valor formateado: '{valor_formateado}'")
print(f"Valor str completo: '{valor_str}'")
print(f"Entero: '{entero}'")
print(f"Decimal: '{decimal}'")
print(f"Longitud entero: {len(entero)}")
print(f"Longitud decimal: {len(decimal)}")

# Analizar carácter por carácter
print("\nAnálisis carácter por carácter del decimal:")
for i, char in enumerate(decimal):
    print(f"  Posición {i}: '{char}' (ASCII: {ord(char)})")
