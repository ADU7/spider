import requests
from scrapy.selector import Selector
import pymysql


conn = pymysql.connect(host="127.0.0.1", user="root", passwd="root", db="spider", charset="utf8")
cursor = conn.cursor()


def crawl_ips():
    # 爬去西刺的免费ip代理
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
    for i in range(3374):
        re = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)
        selector = Selector(text=re.text)
        all_trs = selector.css("#ip_list tr")
        ip_list = []
        for tr in all_trs[1:]:
            speed = tr.css(".bar::attr(title)").extract_first()
            if speed:
                speed = float(speed.split("秒")[0])
            all_texts = tr.css("td::text").extract()
            ip = all_texts[0]
            port = all_texts[1]
            proxy_type = all_texts[5]

            ip_list.append((ip, port, proxy_type, speed))

        for ip_inf in ip_list:
            cursor.execute(
                "INSERT proxy_ip(ip, port, proxy_type, speed) VALUES('{0}', '{1}', '{2}', '{3}')".format(
                    ip_inf[0], ip_inf[1], ip_inf[2], ip_inf[3]
                )
            )
            conn.commit()


class GetIP(object):

    def delete_ip(self, ip):
        # 从数据库中删除无效的ip
        delete_sql = """
                    delete from proxy_ip where ip='{0}'
                """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, proxy_type, ip, port):
        # 判断ip是否可用
        proxy_type = proxy_type.lower()
        http_url = "http://www.baidu.com"
        proxy_url = "{0}://{1}:{2}".format(proxy_type, ip, port)
        try:
            proxy_dict = {
                "{0}".format(proxy_type): proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        random_sql = """
            SELECT proxy_type, ip, port FROM proxy_ip WHERE proxy_type = "HTTP" OR 
            proxy_type = "HTTPS" ORDER BY RAND() LIMIT 1
        """
        cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            proxy_type = ip_info[0]
            ip = ip_info[1]
            port = ip_info[2]

            judge_ip = self.judge_ip(proxy_type, ip, port)
            if judge_ip:
                proxy_type = proxy_type.lower()
                return "{0}://{1}:{2}".format(proxy_type, ip, port)
            else:
                return self.get_random_ip()


# crawl_ips()

if __name__ ==  "__main__":
    get_ip = GetIP()
    print(get_ip.get_random_ip())