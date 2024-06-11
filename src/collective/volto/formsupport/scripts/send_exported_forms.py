# -*- coding: utf-8 -*-
from AccessControl.SecurityManagement import newSecurityManager
from collective.volto.formsupport import _
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from logging import getLogger
from plone import api
from plone.registry.interfaces import IRegistry
from plone.volto.interfaces import IVoltoSettings
from Products.CMFCore.interfaces import IContentish
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest

import click
import csv
import sys
import transaction


LAST_SENDING_DATE_KEY = "collvective.volto.formsupport.LAST_SENDING_DATE"

logger = getLogger(__name__)


@click.command(
    help="bin/instance -OPlone run bin/formsupport_data_cleansing [--dryrun|--no-dryrun]",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.option(
    "--dryrun/--no-dryrun",
    is_flag=True,
    default=True,
    help="--dryrun (default) simulate, --no-dryrun actually save the changes",
)
def main(dryrun):
    def send_csv_email(context, csv_file, recipients):
        host = api.portal.get_tool("MailHost")
        portal_state = api.content.get_view(
            name="plone_portal_state",
            context=api.portal.get(),
            request=getRequest(),
        )
        portal_url = portal_state.navigation_root_url()
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IVoltoSettings, prefix="volto", check=False)
        settings_frontend_domain = getattr(settings, "frontend_domain", None)
        if (
            settings_frontend_domain
            and settings_frontend_domain != "http://localhost:3000"
        ):
            portal_url = settings_frontend_domain
        if portal_url.endswith("/"):
            portal_url = portal_url[:-1]

        mfrom = api.portal.get_registry_record("plone.email_from_address")
        mail_attachment_filename = (
            "FORMS_"
            + context.Title()
            + "_"
            + datetime.today().strftime("%Y-%m-%d")
            + ".csv"
        )

        csv_file.seek(0)

        mail_attachment = MIMEApplication(
            csv_file.read(),
            Name=mail_attachment_filename,
        )
        mail_attachment["Content-Type"] = "text/csv"
        mail_attachment["Content-Disposition"] = (
            'attachment; filename="%s"' % mail_attachment_filename
        )

        for recipient in recipients:
            if not recipient:
                continue
            msg = MIMEMultipart()
            msg.attach(
                MIMEText(
                    api.portal.translate(
                        _(
                            "Your forms export from {url} , until the {date}",
                        )
                    ).format(
                        url=portal_url
                        + "/"
                        + "/".join(context.getPhysicalPath()).replace(
                            "/" + api.portal.get().Title(), ""
                        ),
                        date=datetime.today().strftime("%Y-%m-%d"),
                    ),
                    "html",
                )
            )
            msg["Subject"] = api.portal.translate(
                _("Periodic export of compiled forms")
            )
            msg["From"] = mfrom
            msg["To"] = recipient
            msg.attach(mail_attachment)

            try:
                host.send(msg, charset="utf-8")
            except Exception as e:
                logger.error(
                    f"Could not send periodic form export for {'/'.join(context.getPhysicalPath())}"
                )

    request = getRequest()

    newSecurityManager(api.portal.get(), api.portal.get().getOwner())

    with api.env.adopt_roles(["Manager"]):
        for brain in api.content.find(object_provides=IContentish):
            data = []
            item = brain.getObject()
            annotations = IAnnotations(item)

            try:
                last_sending_date = annotations.get(LAST_SENDING_DATE_KEY, None)

                if not last_sending_date:
                    last_sending_date = datetime(1970, 1, 1, 0, 0, 0)

                else:
                    last_sending_date = datetime.fromisoformat(last_sending_date)

            except ValueError:
                logger.warning(
                    f"Could not convert {'/'.join(item.getPhysicalPath())} 's date"
                )

            csv_export_view = queryMultiAdapter(
                (item, request),
                name="GET_application_json_@form-data-export",
            )

            if not csv_export_view:
                continue

            export = csv_export_view.get_data()

            if export != '"date"\r\n':
                csv_file = csv.DictReader(StringIO(export))

                for i in csv_file:
                    try:
                        date = datetime.fromisoformat(i.get("date"))
                    except ValueError:
                        logger.warning(f"Could not convert {str(i)}'s date")
                        continue

                    if date > last_sending_date:
                        data.append(i)

                if not data:
                    continue

                # In case we have additional columns
                keys = set()
                for i in data:
                    for j in i.keys():
                        keys.add(j)
                for i in data:
                    for j in keys:
                        if not i.get(j):
                            i[j] = None

                recipients = [
                    i.strip()
                    for i in csv_export_view.form_block.get("default_to", "").split(",")
                ]
                csv_stream = StringIO()
                csv_writer = csv.DictWriter(csv_stream, fieldnames=data[0].keys())

                csv_writer.writeheader()
                for i in data:
                    csv_writer.writerow(i)

                send_csv_email(item, csv_stream, recipients)

                annotations[LAST_SENDING_DATE_KEY] = datetime.today().isoformat()

    if not dryrun:
        transaction.commit()


if __name__ == "__main__":
    sys.exit(main())
